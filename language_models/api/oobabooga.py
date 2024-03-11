from typing import Any, Dict, Sequence
import requests
import json
from language_models.api.base import ApiModel
from language_models.formatters.base import PromptFormatter
from language_models.model_message import ModelMessage

from language_models.model_response import ModelResponse


class OobaboogaModel(ApiModel):
    def __init__(
        self,
        host_url: str,
        host_port: str,
        prompt_formatter: PromptFormatter,
        model_path: str,
    ):
        super().__init__(model_path, prompt_formatter)

        self.host_url = host_url
        self.host_port = host_port

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

        request: Dict[str, Any] = {
            "prompt": prompt,
            "max_new_tokens": max_tokens,
            "do_sample": True,
            "temperature": temperature,
            "top_p": 0.1,
            "typical_p": 1,
            "repetition_penalty": 1.18,
            "top_k": 40,
            "min_length": 0,
            "no_repeat_ngram_size": 0,
            "num_beams": 1,
            "penalty_alpha": 0,
            "length_penalty": 1,
            "early_stopping": False,
            "seed": -1,
            "add_bos_token": True,
            "truncation_length": 2048,
            "ban_eos_token": False,
            "skip_special_tokens": True,
            "stopping_strings": [],
        }

        with open("_input.txt", "w", encoding="utf8") as file:
            file.write(str(prompt))

        url = f"http://{self.host_url}:{self.host_port}/v1/completions"

        response = requests.post(url, json=request)

        with open("_output.json", "w") as file:
            json.dump(response.json(), file)

        if response.status_code == 200:
            return ModelResponse(response.json()["choices"][0]["text"].strip(), "")

        return ModelResponse("", "")
