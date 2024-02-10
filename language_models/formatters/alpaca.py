from typing import List
from language_models.formatters.base import PromptFormatter
from language_models.model_message import ModelMessage


class AlpacaFormatter(PromptFormatter):
    def __init__(self):
        super().__init__()
        self.model_type = "ALPACA"

    def generate_prompt(self, messages: List[ModelMessage], use_metadata: bool = False):
        prompt = ""

        for message in messages:
            if message.is_system_message():
                prompt += f"### Instruction:\n{message.get_message(use_metadata)}\n\n"
            elif message.is_user_message():
                prompt += f"### Input:\n{message.get_message(use_metadata)}\n\n"
            elif message.is_assistant_message():
                prompt += f"### Response:\n{message.get_message(use_metadata)}\n\n"

        prompt += f"### Response:\n"

        return prompt
