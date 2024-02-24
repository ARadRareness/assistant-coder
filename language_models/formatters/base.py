from typing import List, Sequence, Union

from language_models.model_message import ModelMessage


class PromptFormatter:
    def __init__(self, model_type: str = ""):
        self.model_type = model_type

    def generate_prompt(
        self, messages: Sequence[ModelMessage], use_metadata: bool = False
    ) -> str | List[Union[int, str]]:
        prompt = ""

        for message in messages:
            prompt += f"<|im_start|>{message.get_role()}\n{message.get_message(use_metadata)}<|im_end|>\n"

        return prompt.strip() + "<|im_start|>assistant"
