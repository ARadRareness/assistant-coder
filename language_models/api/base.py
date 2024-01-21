from typing import List
from language_models.formatters.base import PromptFormatter
from language_models.model_message import ModelMessage
from language_models.model_response import ModelResponse


class Model:
    def __init__(
        self,
        host_url: str,
        host_port: str,
        prompt_formatter: PromptFormatter,
        model_path: str,
    ):
        self.host_url = host_url
        self.host_port = host_port
        self.prompt_formatter = prompt_formatter
        self.model_path = model_path

    def generate_text(
        self,
        messages: List[ModelMessage],
        max_tokens: int = 200,
        temperature: float = 0.2,
        use_metadata: bool = False,
    ):
        return ModelResponse("TEXT", "MODEL_NAME")
