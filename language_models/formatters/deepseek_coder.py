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
                system_message = message.get_message()
            else:
                instruction_messages.append(message)

        instruction = ""

        if len(instruction_messages) == 1:
            instruction = instruction_messages[0].get_message()
        else:
            for message in instruction_messages:
                if message.is_user_message():
                    instruction += f"\n### USER:\n{message.get_message()}"
                elif message.is_reflection_message():
                    instruction += f"\n### REFLECTION:\n{message.get_message()}"
                elif message.is_tool_output_message():
                    instruction += f"\n### TOOL OUTPUT:\n{message.get_message()}"
                else:
                    instruction += f"\n### ASSISTANT:\n{message.get_message()}"

        return f"{system_message}\n### Instruction:\n{instruction}\n### Response:"
