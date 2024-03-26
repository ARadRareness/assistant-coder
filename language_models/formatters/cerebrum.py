from typing import Sequence
from language_models.formatters.base import PromptFormatter
from language_models.model_message import ModelMessage


class CerebrumFormatter(PromptFormatter):
    def __init__(self):
        super().__init__("CEREBRUM")

    def generate_prompt(
        self, messages: Sequence[ModelMessage], use_metadata: bool = False
    ) -> str:
        prompt = "<s>"

        system_message = ""

        for i, message in enumerate(messages):
            if message.is_system_message():
                system_message = message.get_message(use_metadata)
            elif message.is_user_message():
                if system_message and self.is_last_message(messages, i):
                    prompt += f"{system_message}\n"
                    system_message = ""

                prompt += f"User: {message.get_message(use_metadata)}\n"
            elif message.is_assistant_message():
                prompt += f"AI: {message.get_message(use_metadata)}\n"

        prompt += f"AI:"

        return prompt

    def is_last_message(self, messages: Sequence[ModelMessage], i: int) -> bool:
        return i == len(messages) - 1
