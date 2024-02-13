import json
from language_models.constants import JSON_ERROR_MESSAGE
from language_models.helpers.json_parser import handle_json
from language_models.helpers.tool_helper import load_available_tools
from language_models.model_message import MessageMetadata, ModelMessage, Role
from language_models.model_response import ModelResponse


class ToolManager:
    def __init__(self):
        self.tools = load_available_tools()

    def get_tool_conversation(self, message: ModelMessage):
        content = "Using the user message and the available tools, reply with what tool and arguments you want to use to solve the problem."

        content += "Available tools:\n"

        for tool in self.tools:
            content += f"{tool.name} - {tool.description}\n"
            if tool.arguments:
                content += " AVAILABLE ARGUMENTS\n"
                for argument in tool.arguments:
                    content += f" {argument[0]} - {argument[1]}\n"
            content += "\n"

        content += (
            "\n\nAnswer with the optimal tool and arguments to solve the user problem."
        )

        tool_system_message = ModelMessage(Role.SYSTEM, content, message.get_metadata())

        messages = [tool_system_message]

        for tool in self.tools:
            for example_message in tool.get_example_messages():
                messages.append(example_message)

        messages.append(message)
        return messages

    def get_function(self, command):
        target_tool = command["tool"].replace("\\", "")
        for tool in self.tools:
            if target_tool == tool.name:
                return tool.action

        return None

    def add_backslashes(self, response: str):
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

    def parse_and_execute(self, response: ModelResponse, metadata: MessageMetadata):
        try:
            response_text = response.get_text().strip()
            handled_text = handle_json(response_text).replace("\\_", "_")
            handled_text = self.add_backslashes(handled_text)

            command = json.loads(handled_text)

            if not "tool" in command:
                print(f"MISSING tool in: {response_text}")

            if not "arguments" in command:
                command["arguments"] = []

            func = self.get_function(command)

            print("COMMAND", command)

            if func:
                return func(command["arguments"], metadata), handled_text
            else:
                return None, handled_text

        except Exception as e:
            print(f"FAILED TO PARSE: {response_text}")
            print(f"Exception message: {str(e)}")
            return JSON_ERROR_MESSAGE, response_text
