from typing import Sequence
from language_models.formatters.base import PromptFormatter
from language_models.model_message import ModelMessage
from language_models.model_response import ModelResponse


class ApiModel:
    def __init__(self, model_path: str, prompt_formatter: PromptFormatter):
        self.model_path = model_path
        self.prompt_formatter = prompt_formatter

    def generate_text(
        self,
        messages: Sequence[ModelMessage],
        max_tokens: int = 200,
        temperature: float = 0.2,
        use_metadata: bool = False,
    ) -> ModelResponse:
        return ModelResponse("TEXT", "MODEL_NAME")
