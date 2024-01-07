import os
import subprocess

from language_models.api.llamacpp import LlamaCppModel
from language_models.formatters.deepseek_coder import DeepseekCoderFormatter
from language_models.formatters.mistral import MistralFormatter
from language_models.formatters.base import PromptFormatter
from language_models.formatters.neural_chat import NeuralChatFormatter


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

    def load_model(self):
        if self.popen:
            # Terminate the existing process
            self.popen.terminate()
            self.models.pop()

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
                os.path.join("models", self.model_paths[0]),
            ],
        )

        #    stdout=subprocess.DEVNULL,
        #   stderr=subprocess.DEVNULL)

        prompt_formatter = self.get_prompt_formatter(self.model_paths[0])
        self.models.append(
            LlamaCppModel(
                "127.0.0.1", str(self.start_port), prompt_formatter, self.model_paths[0]
            )
        )

        # TODO: Add check whether the process was started successfully or not

    def get_prompt_formatter(self, model_path: str):
        # TODO: Read model type through metadata rather than name
        if "mistral" in model_path or "mixtral" in model_path:
            return MistralFormatter()
        elif "neural" in model_path:
            return NeuralChatFormatter()
        elif "deepseek" in model_path:
            return DeepseekCoderFormatter()
        else:
            return PromptFormatter()

    def __del__(self):
        # Terminate the process if it is still running
        if self.popen:
            self.popen.kill()
            self.popen = None
