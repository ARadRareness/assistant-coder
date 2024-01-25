from typing import List

from language_models.model_message import ModelMessage


class PromptFormatter:
    def __init__(self):
        self.model_type = ""

    def generate_prompt(self, messages: List[ModelMessage], use_metadata: bool = False):
        prompt = ""

        for message in messages:
            prompt += f"<|im_start|>{message.get_role()}\n{message.get_message(use_metadata)}<|im_end|>\n"

        return prompt.strip() + "<|im_start|>assistant"
