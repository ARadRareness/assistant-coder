from typing import List
from language_models.formatters.base import PromptFormatter
from language_models.model_message import ModelMessage


class OrcaHashesFormatter(PromptFormatter):
    def __init__(self):
        super().__init__()
        self.model_type = "NEURAL-CHAT"

    def generate_prompt(self, messages: List[ModelMessage], use_metadata: bool = False):
        prompt = ""

        for message in messages:
            if message.is_user_message():
                prompt += f"### User:\n{message.get_message(use_metadata)}\n"
            elif message.is_assistant_message():
                prompt += f"### Assistant:\n{message.get_message(use_metadata)}\n"
            elif message.is_system_message():
                prompt += f"### System:\n{message.get_message(use_metadata)}\n"

        prompt += f"### Assistant:"

        return prompt
