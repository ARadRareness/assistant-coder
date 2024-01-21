from typing import List
from language_models.formatters.base import PromptFormatter
from language_models.model_message import ModelMessage


class MistralFormatter(PromptFormatter):
    def __init__(self):
        super().__init__()
        self.model_type = "MISTRAL"

    def generate_prompt(self, messages: List[ModelMessage], use_metadata: bool = False):
        prompt = ""

        system_message = ""

        for message in messages:
            if message.is_user_message() or message.is_reflection_message():
                if system_message:
                    prompt += f"[INST] #SYSTEM MESSAGE: {system_message}\n{message.get_message(use_metadata)} [/INST]"
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
