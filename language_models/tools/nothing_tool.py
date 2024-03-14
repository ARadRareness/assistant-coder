from typing import Any, Dict, List
from language_models.api.base import ApiModel
from language_models.model_message import MessageMetadata, ModelMessage
from language_models.tools.base_tool import BaseTool


class NothingTool(BaseTool):
    def __init__(self):
        super().__init__(
            "nothing",
            "if no other tool is applicable, use this tool to do nothing",
            [],
        )

    def action(
        self,
        arguments: Dict[str, Any],
        model: ApiModel,
        messages: List[ModelMessage],
        metadata: MessageMetadata,
    ) -> str:
        return ""

    def get_example_messages(self) -> List[ModelMessage]:
        return self.get_example_dialogue(
            "Say something funny!", '{"tool": "nothing", "arguments": {}}'
        )
