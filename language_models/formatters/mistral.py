from typing import List
from language_models.formatters.base import PromptFormatter
from language_models.model_message import ModelMessage


# This formatter seems to not be able to produce reliable results, probably due to <s> not expected to be an ordinary string token
class MistralFormatter(PromptFormatter):
    def __init__(self):
        super().__init__()
        self.model_type = "MISTRAL"

    def generate_prompt(self, messages: List[ModelMessage], use_metadata: bool = False):
        prompt = "<s>"

        system_message = ""

        for message in messages:
            if message.is_user_message() or message.is_reflection_message():
                if system_message:
                    prompt += (
                        f"[INST] This is the system prompt of the message:\n"
                        f"{system_message}\n"
                        f"This is the user message:\n"
                        f"{message.get_message(use_metadata)} [/INST]"
                    )
                    system_message = ""
                else:
                    prompt += f"[INST] {message.get_message(use_metadata)} [/INST]"
            elif message.is_assistant_message():
                prompt += f"{message.get_message(use_metadata)}</s> "
            elif message.is_system_message():
                system_message = message.get_message(use_metadata)
            elif message.is_reflection_message():
                system_message = message.get_message(use_metadata)
            elif message.is_tool_output_message():
                system_message = message.get_message(use_metadata)

        return prompt
