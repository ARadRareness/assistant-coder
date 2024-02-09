from typing import List
from language_models.formatters.base import PromptFormatter
from language_models.model_message import ModelMessage


# This formatter seems to not be able to produce reliable results, probably due to <s> not expected to be an ordinary string token
class MistralFormatter(PromptFormatter):
    def __init__(self):
        super().__init__()
        self.model_type = "MISTRAL"

        self.BOS = 1
        self.EOS = 2

    def user_message(self, message, use_metadata, system_message, tool_message):
        prompt_message = []
        if system_message:
            prompt_message.append(system_message)
        if tool_message:
            prompt_message.append(tool_message)

        if message:
            prompt_message.append(message.get_message(use_metadata))

        prompt_message = "\n".join(prompt_message)
        return f"[INST] {prompt_message} [/INST]"

    def generate_prompt(self, messages: List[ModelMessage], use_metadata: bool = False):
        prompt = [self.BOS]

        system_message = ""
        tool_message = ""

        for message in messages:
            if message.is_user_message() or message.is_reflection_message():
                prompt.append(
                    self.user_message(
                        message, use_metadata, system_message, tool_message
                    )
                )
                system_message = ""
                tool_message = ""
            elif message.is_assistant_message():
                prompt.append(f"{message.get_message(use_metadata)}")
                prompt.append(self.EOS)
            elif message.is_system_message():
                system_message = message.get_message(use_metadata)
            elif message.is_reflection_message():
                system_message = message.get_message(use_metadata)
            elif message.is_tool_output_message():
                tool_message = message.get_message(use_metadata)

        if system_message or tool_message:
            prompt.append(
                self.user_message(None, use_metadata, system_message, tool_message)
            )
        return prompt
