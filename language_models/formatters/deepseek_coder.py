from typing import List
from language_models.formatters.base import PromptFormatter
from language_models.model_message import ModelMessage


class DeepseekCoderFormatter(PromptFormatter):
    def __init__(self):
        super().__init__()
        self.model_type = "DEEPSEEK_CODER"

    def generate_prompt(self, messages: List[ModelMessage]):
        system_message = ""

        instruction_messages = []

        for message in messages:
            if message.is_system_message():
                system_message = message.get_content()
            else:
                instruction_messages.append(message)

        instruction = ""

        if len(instruction_messages) == 1:
            instruction = instruction_messages[0].get_content()
        else:
            for message in instruction_messages:
                if message.is_user_message():
                    instruction += f"\n### USER:\n{message.get_content()}"
                else:
                    instruction += f"\n### ASSISTANT:\n{message.get_content()}"

        return f"{system_message}\n### Instruction:\n{instruction}\n### Response:"
