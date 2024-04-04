import subprocess
import sys
from typing import Any, Dict, List, Tuple
from language_models.api.base import ApiModel
from language_models.helpers.dangerous_code_detector import DangerousCodeDetector
from language_models.model_message import MessageMetadata, ModelMessage, Role
from language_models.model_state import ModelState
from language_models.tools.base_tool import BaseTool
import tempfile
import os


class CodeInterpreterTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="code_interpreter",
            description="Using this tool, you are able to execute Python code to solve problems.",
            available_arguments=[],
            ask_permission_to_run=False,
        )
        self.dangerous_code_detector = DangerousCodeDetector()

    def run_code(
        self,
        model: ApiModel,
        coding_conversation: List[ModelMessage],
        metadata: MessageMetadata,
    ):
        tries = 3
        for _ in range(tries):
            code_response = model.generate_text(
                messages=coding_conversation,
                max_tokens=2000,
            )

            print(("RESPONSE", code_response.get_text()))

            code = self.parse_code(code_response.get_text())

            print(("CODE", code))

            if code:
                if self.dangerous_code_detector.detect_potentially_dangerous_code(code):
                    if (
                        metadata.ask_permission_to_run_tools
                        and not self.get_user_permission(
                            self.get_permission_message(code)
                        )
                    ):
                        return "User denied permission to run code_interpreter."

                result, result_code = self.execute_python_code(code)
                if result_code == 0:
                    return result
                else:
                    coding_conversation.append(
                        ModelMessage(Role.USER, result, metadata)
                    )
            else:
                return "Error executing code."
        return None

    def action(
        self,
        arguments: Dict[str, Any],
        model: ApiModel,
        messages: List[ModelMessage],
        metadata: MessageMetadata,
    ) -> str:
        coding_conversation = messages + [
            ModelMessage(
                Role.SYSTEM,
                f"You are an expert at solving problems using Python.",
                metadata,
            ),
            ModelMessage(
                Role.USER,
                f"Write python code to solve the problem described in the earlier conversation.",
                metadata,
            ),
        ]

        code_generator_model = os.getenv("MODEL.CODE_GENERATOR")
        try:
            code_generator_gpu_layers = int(
                os.getenv("MODEL.CODE_GENERATOR.GPU_LAYERS", "-1")
            )
        except:
            code_generator_gpu_layers = -1

        original_model = model

        model_manager = ModelState.get_instance().get_model_manager()

        if code_generator_model and model_manager:
            model_manager.change_model(code_generator_model, code_generator_gpu_layers)
            model = model_manager.active_models[0]

        result = None
        try:
            result = self.run_code(model, coding_conversation, metadata)
        except:
            pass

        if code_generator_model and model_manager:
            model_manager.change_model(original_model.model_path)

        if result:
            return result

        return "No code to execute."

    def execute_python_code(self, code: str) -> Tuple[str, int]:
        """
        Executes the given Python code in a temporary file and captures the output.
        If the execution takes longer than 20 seconds, it is aborted.

        Args:
            code (str): The Python code to execute.

        Returns:
            str: The output of the executed code or an error message.
            int: The result code, 0 for success, -1 for failure or timeout.
        """
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp_file:
            tmp_file_name = tmp_file.name
            tmp_file.write(code.encode("utf-8"))
            tmp_file.flush()

        try:
            output = subprocess.run(
                [sys.executable, tmp_file_name],
                capture_output=True,
                text=True,
                check=True,
                timeout=20,
            )
            return (
                f'When answering the user, pretend that you have executed Python code and received the following output: "{output.stdout}"',
                0,
            )
        except subprocess.TimeoutExpired:
            return "Error executing code: Execution time exceeded 20 seconds.", -1
        except subprocess.CalledProcessError as e:
            return f"Error executing code: {e.stderr}", -1
        finally:
            os.remove(tmp_file_name)

    def get_permission_message(self, code: str) -> str:
        if code:
            return f"AC would like to execute the following Python code:\n\n{code}\n\nDo you want to allow this?"
        else:
            return ""

    def get_code_argument(self, arguments: Dict[str, Any]) -> str:
        if "CODE" in arguments:
            return arguments["CODE"].replace("\\\\n", "\n").replace('"""', '"')
        return ""

    def get_example_messages(self) -> List[ModelMessage]:
        return []

    def parse_code(self, message: str) -> str:
        """
        Parses the Python code from a language model's message, assuming the code is
        presented in a markdown code block format.

        Args:
            message (str): The message containing the Python code.

        Returns:
            str: The extracted Python code.
        """
        # Looking for the start of the code block
        start = message.find("```python")
        if start != -1:
            # Adjusting start to the actual beginning of the code
            start += len("```python")
            end = message.find("```", start)
            if end != -1:
                return message[start:end].strip()
        return ""
