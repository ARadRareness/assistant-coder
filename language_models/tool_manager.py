import json, subprocess, sys
from typing import Dict, Optional, Sequence, Tuple
from language_models.constants import JSON_ERROR_MESSAGE
from language_models.helpers.json_parser import handle_json
from language_models.helpers.tool_helper import load_available_tools
from language_models.model_message import MessageMetadata, ModelMessage, Role
from language_models.model_response import ModelResponse
from language_models.tools.base_tool import BaseTool


class ToolManager:
    def __init__(self):
        self.tools: Sequence[BaseTool] = load_available_tools()

    def get_tool_conversation(self, message: ModelMessage) -> Sequence[ModelMessage]:
        content = "Using the user message and the available tools, reply with what tool and arguments you want to use to solve the problem."

        content += "Available tools:\n"

        for tool in self.tools:
            content += f"{tool.name} - {tool.description}\n"
            arguments = tool.get_available_arguments()
            if arguments:
                content += " AVAILABLE ARGUMENTS\n"
                for argument in arguments:
                    content += f" {argument[0]} - {argument[1]}\n"
            content += "\n"

        content += "\n\nAnswer with the optimal tool and arguments to solve the provided problem. It is essential that you use the best tool and arguments to solve the problem."

        tool_system_message = ModelMessage(Role.SYSTEM, content, message.get_metadata())

        messages = [tool_system_message]

        for tool in self.tools:
            for example_message in tool.get_example_messages():
                messages.append(example_message)

        messages.append(message)
        return messages

    def get_target_tool(self, command: Dict[str, str]) -> Optional[BaseTool]:
        target_tool: str = command["tool"].replace("\\", "")
        for tool in self.tools:
            if target_tool == tool.name:
                return tool

        return None

    def add_backslashes(self, response: str) -> str:
        """Not so pretty hack to inject backslashes into string
        since json.loads requires 4 backslashes to indicate paths
        and the llm usually only outputs one or two.
        """
        new_response = ""

        i = 0

        while i < len(response):
            c = response[i]
            if c == "\\":
                for j in range(3):
                    new_response += "\\"

                for j in range(1, 4):
                    if len(response) > j + i and response[j + i] == "\\":
                        i += 1
                    else:
                        break

            new_response += c
            i += 1

        return new_response

    def parse_and_execute(
        self, response: ModelResponse, metadata: MessageMetadata
    ) -> Tuple[str, str]:
        response_text = ""

        try:
            response_text = response.get_text().strip()
            handled_text = handle_json(response_text).replace("\\_", "_")
            handled_text = self.add_backslashes(handled_text)

            command = json.loads(handled_text)

            if not "tool" in command:
                print(f"MISSING tool in: {response_text}")

            if not "arguments" in command:
                command["arguments"] = []

            target_tool = self.get_target_tool(command)

            print("COMMAND", command)

            if target_tool:
                if metadata.ask_permission_to_run_tools:
                    if target_tool.ask_permission_to_run:
                        permission_message = target_tool.ask_permission_message(
                            command["arguments"], metadata
                        )

                        if not permission_message:
                            permission_message = "UNKNOWN PERMISSION MESSAGE"

                        if not self.get_user_permission(permission_message):
                            print(f"User denied permission to run {target_tool.name}")
                            return "", handled_text

                return target_tool.action(command["arguments"], metadata), handled_text
            else:
                return "", handled_text

        except Exception as e:
            print(f"FAILED TO PARSE: {response_text}")
            print(f"Exception message: {str(e)}")
            return JSON_ERROR_MESSAGE, response_text

    def get_user_permission(self, message: str):
        result = subprocess.call(
            [sys.executable, "language_models/helpers/permission_notifier.py", message]
        )
        return result == 0
