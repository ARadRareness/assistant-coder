import os
import subprocess

from language_models.api.llamacpp import LlamaCppModel
from language_models.formatters.deepseek_coder import DeepseekCoderFormatter
from language_models.formatters.mistral import MistralFormatter
from language_models.formatters.base import PromptFormatter
from language_models.formatters.orca_hashes import OrcaHashesFormatter


class ModelManager:
    def __init__(self, llama_cpp_path, start_port, model_paths):
        self.llama_cpp_path = llama_cpp_path
        self.start_port = start_port
        self.model_paths = model_paths
        self.popen = None
        self.gpu_layers = 9001
        self.context_window = 2048
        self.models = []

    def model_is_loaded(self):
        return self.popen

    def load_model(self, model_index=0):
        if self.popen:
            # Terminate the existing process
            self.popen.terminate()
            self.models.pop()

        model_path = os.path.join("models", self.model_paths[model_index])

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
        )

        #    stdout=subprocess.DEVNULL,
        #   stderr=subprocess.DEVNULL)

        prompt_formatter = self.get_prompt_formatter(self.model_paths[model_index])
        self.models.append(
            LlamaCppModel(
                "127.0.0.1",
                str(self.start_port),
                prompt_formatter,
                self.model_paths[model_index],
            )
        )

        # TODO: Add check whether the process was started successfully or not

    def read_prompt_format(self, model_path: str):
        from gguf import GGUFReader

        reader = GGUFReader(model_path, "r+")

        if "tokenizer.chat_template" in reader.fields:
            jinja_template = "".join(
                [chr(c) for c in reader.fields["tokenizer.chat_template"].parts[4]]
            )
            return jinja_template
        else:
            print("No chat template found.")

    def get_prompt_formatter(self, model_path: str):
        # TODO: Read model type through metadata rather than name
        if "mistral" in model_path or "mixtral" in model_path:
            return MistralFormatter()
        elif "neural" in model_path or "solar" in model_path:
            return OrcaHashesFormatter()
        elif "deepseek" in model_path:
            return DeepseekCoderFormatter()
        else:
            return PromptFormatter()

    def change_model(self, model_path: str):
        model_index = self.model_paths.index(model_path)

        if model_index == -1:
            print(f"Error: Model {model_path} not found.")
            return

        self.load_model(model_index)

    def get_available_models(self):
        return self.model_paths

    def __del__(self):
        # Terminate the process if it is still running
        if self.popen:
            self.popen.kill()
            self.popen = None
