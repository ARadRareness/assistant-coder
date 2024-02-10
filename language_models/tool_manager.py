import datetime
import json
import os
from language_models.constants import JSON_ERROR_MESSAGE
from language_models.model_message import MessageMetadata, ModelMessage, Role
from language_models.model_response import ModelResponse


class Tool:
    def __init__(self, name, description, arguments, tool_function):
        self.name = name
        self.description = description
        self.arguments = arguments
        self.tool_function = tool_function


def read_file(arguments):
    if "FILEPATH" in arguments:
        fpath = arguments["FILEPATH"]
        print(f"READ FILE with filepath {fpath}!")
        if os.path.isfile(fpath):
            with open(fpath, "r", encoding="utf8") as f:
                return f"FILE CONTENT OF {fpath}:\n{f.read()}"
        else:
            print("FILE WAS NOT FOUND!")
    else:
        print("READ FILE with UNKNOWN ARGUMENTS")


class ToolManager:
    def __init__(self):
        self.tools = [
            Tool(
                "read_file",
                "read the content of a specific file",
                [
                    (
                        "FILEPATH",
                        "(MANDATORY) specifies the filepath of the file to read, only one file is allowed",
                    )
                ],
                read_file,
            ),
            Tool(
                "get_date_and_time",
                "retrieve the current date and time",
                [],
                lambda _: "The current date and time is: "
                + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                + ". When answering questions about the current date or time, use this information, don't mention not being able to use the current time and/or date.",
            ),
            Tool(
                "nothing",
                "if no other tool is applicable, use this tool to do nothing",
                [],
                None,
            ),
        ]

    def get_tool_conversation(self, message: ModelMessage):
        content = "Using the user message and the available tools, reply with what tool and arguments you want to use to solve the problem. Answer in a json-format, and only with a single json response. Always use one of the tools.\n\n"

        content += "Available tools:\n"

        for tool in self.tools:
            content += f"{tool.name} - {tool.description}\n"
            if tool.arguments:
                content += " AVAILABLE ARGUMENTS\n"
                for argument in tool.arguments:
                    content += f" {argument[0]} - {argument[1]}\n"

        tool_system_message = ModelMessage(Role.SYSTEM, content, message.get_metadata())

        example_path = "C:\\test.txt"

        example_user_message = ModelMessage(
            Role.USER,
            "Read the content of the selected file for me please.",
            MessageMetadata(datetime.datetime.now(), [example_path]),
        )
        example_assistant_message = ModelMessage(
            Role.ASSISTANT,
            '{"tool": "read_file", "arguments": {"FILEPATH": "%s"}}' % (example_path),
            MessageMetadata(datetime.datetime.now(), [example_path]),
        )

        example_user_message2 = ModelMessage(
            Role.USER,
            "Say something funny!",
            MessageMetadata(datetime.datetime.now(), [example_path]),
        )
        example_assistant_message2 = ModelMessage(
            Role.ASSISTANT,
            '{"tool": "nothing", "arguments": {}}',
            MessageMetadata(datetime.datetime.now(), [example_path]),
        )

        messages = [
            tool_system_message,
            example_user_message,
            example_assistant_message,
            example_user_message2,
            example_assistant_message2,
            message,
        ]
        return messages

    def get_function(self, command):
        target_tool = command["tool"].replace("\\", "")
        for tool in self.tools:
            if target_tool == tool.name:
                return tool.tool_function

        return None

    def handle_json(self, response: str):
        level_count = 0
        start_index = -1
        end_index = -1
        for i, char in enumerate(response):
            if char == "{":
                if start_index == -1:
                    start_index = i
                level_count += 1
            elif char == "}":
                level_count -= 1
                if level_count == 0:
                    end_index = i + 1
                    break

        return response[start_index:end_index]

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

    def parse_and_execute(self, response: ModelResponse):
        try:
            response_text = response.get_text().strip()
            handled_text = self.handle_json(response_text).replace("\\_", "_")
            handled_text = self.add_backslashes(handled_text)

            command = json.loads(handled_text)

            if not "tool" in command or not "arguments" in command:
                print(f"MISSING tool or arguments in: {response_text}")

            func = self.get_function(command)

            if func:
                return func(command["arguments"]), handled_text
            else:
                return None, handled_text

        except Exception as e:
            print(f"FAILED TO PARSE: {response_text}")
            print(f"Exception message: {str(e)}")
            return JSON_ERROR_MESSAGE, response_text
