from typing import List
from language_models.formatters.base import PromptFormatter
from language_models.model_message import ModelMessage


class DeepseekCoderFormatter(PromptFormatter):
    def __init__(self):
        super().__init__()
        self.model_type = "DEEPSEEK_CODER"

    def generate_prompt(self, messages: List[ModelMessage]):
        prompt = ""

        system_message = ""

        for message in messages:
            pass  # TODO: Implement me

        return prompt
