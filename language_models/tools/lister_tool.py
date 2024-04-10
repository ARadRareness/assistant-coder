from typing import Any, Dict, List
from language_models.api.base import ApiModel
from language_models.helpers.tool_helper import load_available_tools

from language_models.model_message import MessageMetadata, ModelMessage
from language_models.tools.base_tool import BaseTool


class ListerTool(BaseTool):
    def __init__(self):
        super().__init__(
            "get_available_tools",
            "retrieve a list of available tools",
            [],
        )

        self.tools = load_available_tools(self.__class__.__name__)
        self.tools.append(self)
        self.tools = sorted(self.tools, key=lambda tool: tool.name)

    def action(
        self,
        arguments: Dict[str, Any],
        model: ApiModel,
        messages: List[ModelMessage],
        metadata: MessageMetadata,
    ) -> str:
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
        return "The following tools are available:\n" + "\n".join(
            [f"{tool.name} - {tool.description}" for tool in filtered_tools]
        )

    def get_example_messages(self) -> List[ModelMessage]:
        return []
