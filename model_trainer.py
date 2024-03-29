from datasets import load_dataset

from unsloth import FastLanguageModel

import torch

from language_models.formatters.mistral import MistralFormatter
from language_models.model_message import MessageMetadata, ModelMessage, Role

import datetime

# https://colab.research.google.com/drive/1Dyauq4kTZoLewQ1cApceUQVNcnnNTzg_?usp=sharing#scrollTo=6bZsfBuZDeCL

max_seq_length = 2048  # Choose any! We auto support RoPE Scaling internally!
dtype = (
    None  # None for auto detection. Float16 for Tesla T4, V100, Bfloat16 for Ampere+
)
load_in_4bit = True  # Use 4bit quantization to reduce memory usage. Can be False.

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/mistral-7b-instruct-v0.2-bnb-4bit",  # Choose ANY! eg teknium/OpenHermes-2.5-Mistral-7B
    max_seq_length=max_seq_length,
    dtype=dtype,
    load_in_4bit=load_in_4bit,
    # token = "hf_...", # use one if using gated models like meta-llama/Llama-2-7b-hf
)

model = FastLanguageModel.get_peft_model(
    model,
    r=16,  # Choose any number > 0 ! Suggested 8, 16, 32, 64, 128
    target_modules=[
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    ],
    lora_alpha=16,
    lora_dropout=0,  # Supports any, but = 0 is optimized
    bias="none",  # Supports any, but = "none" is optimized
    use_gradient_checkpointing=True,
    random_state=3407,
    use_rslora=False,  # We support rank stabilized LoRA
    loftq_config=None,  # And LoftQ
)

BOS_TOKEN = tokenizer.bos_token  # Must add BOS_TOKEN
EOS_TOKEN = tokenizer.eos_token  # Must add EOS_TOKEN


def formatting_prompts_func(examples):
    instructions = examples["instruction"]
    inputs = examples["input"]
    outputs = examples["output"]
    texts = []
    formatter = MistralFormatter()
    for instruction, input, output in zip(instructions, inputs, outputs):
        # Must add EOS_TOKEN, otherwise your generation will go on forever!
        messages = [
            ModelMessage(
                Role.USER,
                input,
                MessageMetadata(timestamp=datetime.datetime.now(), selected_files=[]),
            ),
            ModelMessage(
                Role.ASSISTANT,
                output,
                MessageMetadata(timestamp=datetime.datetime.now(), selected_files=[]),
            ),
        ]
        formatted_text = formatter.generate_prompt(messages)

        final_text = ""

        for text_part in formatted_text:
            if text_part == 1:
                final_text += BOS_TOKEN
            elif text_part == 2:
                final_text += EOS_TOKEN
            else:
                final_text += text_part

        texts.append(final_text)

    return {
        "text": texts,
    }


dataset = load_dataset("datasets/ac_tools/", split="train")
dataset = dataset.map(
    formatting_prompts_func,
    batched=True,
)

print(dataset)


from trl import SFTTrainer
from transformers import TrainingArguments

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=max_seq_length,
    dataset_num_proc=2,
    packing=False,  # Can make training 5x faster for short sequences.
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=5,
        max_steps=60,
        learning_rate=2e-4,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=1,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=3407,
        output_dir="outputs",
    ),
)

trainer_stats = trainer.train()

model.save_pretrained_gguf("model", tokenizer, quantization_method="q5_k_m")

# If the line above fails, then run
# python3 llama.cpp/convert.py model
# llama.cpp/build/bin/quantize ./model/ggml-model-f32.gguf ./model/ggml-model-Q5_K_M.gguf Q5_K_M
