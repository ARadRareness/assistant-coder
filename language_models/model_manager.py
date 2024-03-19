import os
import subprocess
import dotenv
from typing import List
from language_models.api.base import ApiModel

from language_models.api.llamacpp import LlamaCppModel
from language_models.formatters.alpaca import AlpacaFormatter
from language_models.formatters.deepseek_coder import DeepseekCoderFormatter
from language_models.formatters.mistral import MistralFormatter
from language_models.formatters.base import PromptFormatter
from language_models.formatters.orca_hashes import OrcaHashesFormatter
from language_models.api.openai import OpenAIModel


class ModelManager:
    def __init__(self, llama_cpp_path: str, start_port: int):
        self.llama_cpp_path = llama_cpp_path
        self.start_port = start_port
        self.popen = None
        self.gpu_layers = 9001
        self.context_window = 2048
        self.active_models: List[ApiModel] = []

    def model_is_loaded(self) -> bool:
        return self.popen != None

    def load_model(self, model_index: int = -1) -> None:
        if model_index == -1:
            last_model_used = os.getenv("LAST_MODEL_USED", "")
            available_models = self.get_available_models()
            try:
                model_index = available_models.index(last_model_used)
            except ValueError:
                model_index = (
                    0  # Default to the first model if last_model_used is not found
                )

        if self.popen:
            # Terminate the existing process
            self.popen.terminate()
            self.active_models.pop()

        available_models = self.get_available_models()

        model_identifier = available_models[model_index]

        # Check if the selected model is the OpenAI model
        if model_identifier == "gpt-3.5-turbo":
            # Load the OpenAI model
            api_key = os.getenv(
                "OPENAI_API_KEY"
            )  # Ensure you have set this environment variable
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set.")
            openai_model = OpenAIModel(api_key=api_key, model_name="gpt-3.5-turbo")
            self.active_models.append(openai_model)
        else:
            # Load a local model
            model_path = os.path.join("models", model_identifier)
            self.read_prompt_format(model_path)
            print(self.llama_cpp_path)

            # Start a new child process with the llama cpp path and the model path as arguments
            self.popen = subprocess.Popen(
                [
                    self.llama_cpp_path,
                    "--n-gpu-layers",
                    str(self.gpu_layers),
                    "--ctx-size",
                    str(self.context_window),
                    "--port",
                    str(self.start_port),
                    "-m",
                    model_path,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            while True:
                if self.popen.stdout:
                    line = self.popen.stdout.readline()
                    print(line, end="")  # You can also log this instead of printing
                    if "Available slots:" in line:
                        break
                else:
                    return

            prompt_formatter = self.get_prompt_formatter(model_identifier)
            self.active_models.append(
                LlamaCppModel(
                    "127.0.0.1",
                    str(self.start_port),
                    prompt_formatter,
                    model_identifier,
                )
            )
            # No need for sleep here as we wait for the specific output

        dotenv_file = dotenv.find_dotenv()
        if dotenv_file:
            dotenv.set_key(dotenv_file, "LAST_MODEL_USED", model_identifier)

    def read_prompt_format(self, model_path: str) -> str:
        from gguf import GGUFReader

        reader = GGUFReader(model_path, "r+")

        if "tokenizer.chat_template" in reader.fields:
            jinja_template = "".join(
                [chr(c) for c in reader.fields["tokenizer.chat_template"].parts[4]]
            )
            return jinja_template
        else:
            print("No chat template found.")
            return ""

    def get_prompt_formatter(self, model_path: str) -> PromptFormatter:
        # TODO: Read model type through metadata rather than name
        if "mistral" in model_path or "mixtral" in model_path:
            return MistralFormatter()
        elif "neural" in model_path or "solar" in model_path:
            return OrcaHashesFormatter()
        elif "deepseek" in model_path:
            return DeepseekCoderFormatter()
        elif "alpaca" in model_path:
            return AlpacaFormatter()
        else:
            return PromptFormatter()

    def change_model(self, model_path: str) -> None:
        for model in self.active_models:
            if model.get_model_path() == model_path:
                return

        model_index = self.get_available_models().index(model_path)

        if model_index == -1:
            print(f"Error: Model {model_path} not found.")
            return

        self.load_model(model_index)

    def get_available_models(self) -> List[str]:
        models = list(filter(lambda f: f.endswith(".gguf"), os.listdir("models")))
        models.append("gpt-3.5-turbo")  # Append the OpenAI model identifier
        return models

    def __del__(self) -> None:
        # Terminate the process if it is still running
        if self.popen:
            self.popen.kill()
            self.popen = None
