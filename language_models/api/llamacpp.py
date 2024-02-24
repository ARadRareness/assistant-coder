from typing import Sequence
import requests
import json
from language_models.api.base import ApiModel
from language_models.formatters.base import PromptFormatter
from language_models.model_message import ModelMessage
from language_models.model_response import ModelResponse


class LlamaCppModel(ApiModel):
    def __init__(
        self,
        host_url: str,
        host_port: str,
        prompt_formatter: PromptFormatter,
        model_path: str,
    ):
        super().__init__(host_url, host_port, prompt_formatter, model_path)

    def generate_text(
        self,
        messages: Sequence[ModelMessage],
        max_tokens: int = 200,
        temperature: float = 0.2,
        use_metadata: bool = False,
    ) -> ModelResponse:
        prompt = self.prompt_formatter.generate_prompt(
            messages, use_metadata=use_metadata
        )
        print(prompt)

        request = {
            "prompt": prompt,
            "n_predict": max_tokens,
            "temperature": temperature,
            "top_p": 0.8,
            "min_p": 0.05,
            "typical_p": 1,
            "repeat_penalty": 1.18,
            "top_k": 40,
        }

        with open("_input.txt", "w", encoding="utf8") as file:
            file.write(str(prompt))

        url = f"http://{self.host_url}:{self.host_port}/completion"

        response = requests.post(url, json=request)

        with open("_output.json", "w") as file:
            json.dump(response.json(), file)

        if response.status_code == 200:
            json_data = response.json()
            return ModelResponse(json_data["content"].strip(), json_data["model"])

        return ModelResponse("", "")
