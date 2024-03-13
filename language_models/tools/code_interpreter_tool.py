import subprocess
import sys
from typing import Any, Dict, List
from language_models.model_message import MessageMetadata, ModelMessage
from language_models.tools.base_tool import BaseTool


class CodeInterpreterTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="code_interpreter",
            description="Using this tool, you are able to execute Python code.",
            available_arguments=[
                (
                    "CODE",
                    "(MANDATORY) specifies the Python code to execute.",
                )
            ],
            ask_permission_to_run=True,
        )

    def action(self, arguments: Dict[str, Any], metadata: MessageMetadata) -> str:
        code = self.get_code_argument(arguments)

        try:
            output = subprocess.run(
                [sys.executable, "-c", code], capture_output=True, text=True, check=True
            )
            return f'Explain your answer using the following output result of the python code: "{output.stdout}"'
        except subprocess.CalledProcessError as e:
            return f"Error executing code: {e.output}"

    def ask_permission_message(
        self, arguments: Dict[str, Any], metadata: MessageMetadata
    ) -> str:
        code = self.get_code_argument(arguments)

        if code:
            return f"AC would like to execute the following Python code:\n\n{code}\n\nDo you want to allow this?"
        else:
            return ""

    def get_code_argument(self, arguments: Dict[str, Any]) -> str:
        if "CODE" in arguments:
            return arguments["CODE"].replace("<", "").replace(">", "")
        return ""

    def get_example_messages(self) -> List[ModelMessage]:
        return self.get_example_dialogue(
            """Run this code for me: 
            print("Hello World!")
            """,
            '{"tool": "code_interpreter", "arguments": {"CODE": "print("Hello World!")"}}',
        )
