from typing import Sequence
from language_models.formatters.base import PromptFormatter
from language_models.model_message import ModelMessage


# This formatter seems to not be able to produce reliable results, probably due to <s> not expected to be an ordinary string token
class Llama3Formatter(PromptFormatter):
    def __init__(self):
        super().__init__("LLAMA3")

    # returns a list containing ints and strings
    def generate_prompt(
        self, messages: Sequence[ModelMessage], use_metadata: bool = False
    ) -> str:
        prompt: str = "<|begin_of_text|>"

        system_message = ""

        for message in messages:
            if message.is_system_message():
                system_message = message.get_message(use_metadata)

        if system_message:
            prompt += self._add_message(system_message, "system")

        for message in messages:
            if message.is_user_message():
                prompt += self._add_message(message.get_message(use_metadata), "user")
            elif message.is_assistant_message():
                prompt += self._add_message(
                    message.get_message(use_metadata), "assistant"
                )

        prompt += "<|start_header_id|>assistant<|end_header_id|>\n\n"
        return prompt

    def _add_message(self, message: str, role: str) -> str:
        return f"<|start_header_id|>{role}<|end_header_id|>\n\n{message}<|eot_id|>"
