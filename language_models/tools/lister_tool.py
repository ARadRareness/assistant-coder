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
        return "The following tools are available:\n" + "\n".join(
            [f"{tool.name} - {tool.description}" for tool in self.tools]
        )

    def get_example_messages(self) -> List[ModelMessage]:
        return []
