import datetime
import json
import os
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
                "nothing",
                "if no other tool is applicable, use this tool to do nothing",
                [],
                None,
            ),
        ]

    def get_tool_conversation(self, message: ModelMessage):
        content = "Using the user message and the available tools, reply with what tool and arguments you want to use to solve the problem. Answer in a json-format.\n\n"

        content += "Available tools:\n"

        for tool in self.tools:
            content += f"{tool.name} - {tool.description}\n"
            if tool.arguments:
                content += " AVAILABLE ARGUMENTS\n"
                for argument in tool.arguments:
                    content += f" {argument[0]} - {argument[1]}\n"

        tool_system_message = ModelMessage(Role.SYSTEM, content, message.get_metadata())

        example_user_message = ModelMessage(
            Role.USER,
            "Read the content of the selected file for me please.",
            MessageMetadata(datetime.datetime.now(), ["C:\\test.txt"]),
        )
        example_assistant_message = ModelMessage(
            Role.ASSISTANT,
            '{"tool": "read_file", "arguments": {"FILEPATH": "C:\\test.txt"}}',
            MessageMetadata(datetime.datetime.now(), ["C:\\test.txt"]),
        )

        messages = [
            tool_system_message,
            example_user_message,
            example_assistant_message,
            message,
        ]
        return messages

    def get_function(self, command):
        for tool in self.tools:
            if command["tool"] == tool.name:
                return tool.tool_function

        return None

    def parse_and_execute(self, response: ModelResponse):
        # try:
        response_text = response.get_text()
        command = json.loads(response_text)

        if not "tool" in command or not "arguments" in command:
            print(f"MISSING tool or arguments in: {response_text}")

        func = self.get_function(command)

        if func:
            return func(command["arguments"])

    # except:
    #    print(f"FAILED TO PARSE: {response_text}")
    #    return None
