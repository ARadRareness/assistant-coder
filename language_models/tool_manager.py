import json
import os
from typing import Any, Dict, Optional, Sequence, Tuple, List
from language_models.api.base import ApiModel
from language_models.helpers.json_fixer import fix_json_errors
from language_models.helpers.json_parser import handle_json
from language_models.helpers.tool_helper import load_available_tools
from language_models.model_message import MessageMetadata, ModelMessage, Role
from language_models.model_response import ModelResponse
from language_models.model_state import ModelState
from language_models.tools.base_tool import BaseTool

SELF_CONTAINED_MODE = True


class ToolManager:
    def __init__(self):
        self.tools: Sequence[BaseTool] = load_available_tools()

    def get_tool_conversation(
        self, message: ModelMessage, tools: Sequence[BaseTool]
    ) -> Sequence[ModelMessage]:
        content = "You are an expert at determining which tool is the best to use in order to solve the problem. Using the user message and the available tools, reply with what tool and arguments you want to use."

        content += "Available tools:\n"

        for tool in tools:
            content += f"{tool.name} - {tool.description}\n"
            arguments = tool.get_available_arguments()
            if arguments:
                content += " AVAILABLE ARGUMENTS\n"
                for argument in arguments:
                    content += f" {argument[0]} - {argument[1]}\n"
            else:
                content += "No arguments available for this tool."
            content += "\n"

        content += "\n\nAnswer with the optimal tool and arguments to solve the provided problem. It is very important to me that you use the best tool and arguments to solve the problem."

        tool_system_message = ModelMessage(Role.SYSTEM, content, message.get_metadata())

        messages = [tool_system_message]

        for tool in tools:
            for example_message in tool.get_example_messages():
                messages.append(example_message)

        messages.append(message)
        return messages

    def get_target_tool(
        self, command: Dict[str, str], tools: Sequence[BaseTool]
    ) -> Optional[BaseTool]:
        target_tool: str = command["tool"].replace("\\", "")
        for tool in tools:
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

    def parse_json(
        self, model: ApiModel, response: ModelResponse, metadata: MessageMetadata
    ) -> Tuple[Dict[str, Any], str]:
        response_text = response.get_text().strip()
        handled_text = handle_json(response_text).replace("\\_", "_")
        handled_text = self.add_backslashes(handled_text)

        try:
            return json.loads(handled_text), handled_text
        except Exception as _:
            result = fix_json_errors(model, metadata, handled_text)
            if result:
                return result, handled_text
            else:
                raise Exception(f"Failed to fix JSON: {handled_text}")

    def parse_tool(
        self,
        model: ApiModel,
        response: ModelResponse,
        metadata: MessageMetadata,
        tools: Sequence[BaseTool],
    ) -> Tuple[Optional[BaseTool], Dict[str, Any]]:
        response_text = response.get_text()
        try:
            command, _ = self.parse_json(model, response, metadata)
            print("COMMAND", command)

            if not "tool" in command:
                print(f"MISSING tool in: {response_text}")

            if not "arguments" in command:
                command["arguments"] = {}

            if not isinstance(command["arguments"], dict):
                command["arguments"] = {}

            target_tool = self.get_target_tool(command, tools)

            return target_tool, command

        except Exception as e:
            print(f"FAILED TO PARSE: {response_text}")
            print(f"Exception message: {str(e)}")
            return None, {}

    def change_to_tool_model(self, model: ApiModel):

        tool_selector_model = os.getenv("MODEL.TOOL_SELECTOR")

        try:
            tool_selector_gpu_layers = int(
                os.getenv("MODEL.TOOL_SELECTOR.GPU_LAYERS", "-1")
            )
        except:
            tool_selector_gpu_layers = -1

        model_manager = ModelState.get_instance().get_model_manager()

        if tool_selector_model and model_manager:
            model_manager.change_model(tool_selector_model, tool_selector_gpu_layers)
            model = model_manager.active_models[0]

        return model, model_manager

    def create_self_contained_query(
        self,
        model: ApiModel,
        max_tokens: int,
        messages: List[ModelMessage],
        use_metadata: bool = False,
    ) -> ModelMessage:
        metadata = messages[-1].get_metadata()
        self_referential_conversation = messages[::] + [
            ModelMessage(
                Role.USER,
                "Rewrite the last message in a self-contained manner, for example by replacing 'run it' with 'run (what it is, based on the context of the conversation)'. Write your response as short as needed to convey the message of the user. Start your response with 'The user...'",
                metadata,
            )
        ]

        response = model.generate_text(
            self_referential_conversation,
            max_tokens=max_tokens,
            use_metadata=use_metadata,
        )

        print("SELF_CONTAINED: " + response.get_text())
        return ModelMessage(Role.USER, response.get_text(), metadata)

    def retrieve_tool_output(
        self,
        model: ApiModel,
        max_tokens: int,
        messages: List[ModelMessage],
        use_metadata: bool = False,
    ) -> str:
        if messages:
            metadata = messages[-1].get_metadata()

            allowed_tools = metadata.allowed_tools

            if allowed_tools is not None:
                filtered_tools = [
                    tool
                    for tool in self.tools
                    if tool.name in allowed_tools
                    or tool.name == "nothing"
                    or tool.name == "get_available_tools"
                ]
            else:
                filtered_tools = self.tools

            query_message: ModelMessage = messages[-1]

            if SELF_CONTAINED_MODE:
                query_message: ModelMessage = self.create_self_contained_query(
                    model, max_tokens, messages, use_metadata
                )

            tool_conversation = self.get_tool_conversation(
                query_message, filtered_tools
            )

            tool_model, model_manager = self.change_to_tool_model(model)

            response = tool_model.generate_text(
                tool_conversation, max_tokens=max_tokens, use_metadata=use_metadata
            )

            tool, command = self.parse_tool(model, response, metadata, filtered_tools)

            if tool:
                if metadata.ask_permission_to_run_tools:
                    if tool.ask_permission_to_run:
                        permission_message = tool.ask_permission_message(
                            command["arguments"], metadata
                        )

                        if not permission_message:
                            permission_message = "UNKNOWN PERMISSION MESSAGE"

                        if not tool.get_user_permission(permission_message):
                            print(f"User denied permission to run {tool.name}")
                            return ""
                result = tool.action(command["arguments"], model, messages, metadata)
            else:
                result = ""

            if tool_model != model and model_manager:
                model_manager.change_model(model.model_path)

            return result
        return ""
