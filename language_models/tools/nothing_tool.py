from language_models.model_message import MessageMetadata
from language_models.tools.base_tool import BaseTool


class NothingTool(BaseTool):
    def __init__(self):
        super().__init__(
            "nothing",
            "if no other tool is applicable, use this tool to do nothing",
            [],
        ),

    def action(self, arguments, metadata: MessageMetadata):
        return None
