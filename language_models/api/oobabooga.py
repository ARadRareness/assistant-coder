from typing import List
import requests
import json
from language_models.api.base import Model
from language_models.model_message import ModelMessage

from language_models.model_response import ModelResponse


class OobaboogaModel(Model):
    def __init__(self, host_url, host_port, prompt_formatter, model_path):
        super().__init__(host_url, host_port, prompt_formatter, model_path)

    def generate_text(
        self,
        messages: List[ModelMessage],
        max_tokens: int = 200,
        temperature: float = 0.2,
        use_metadata: bool = False,
    ):
        prompt = self.prompt_formatter.generate_prompt(
            messages, use_metadata=use_metadata
        )

        request = {
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
