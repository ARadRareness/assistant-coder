import datetime
from typing import Any, Dict, List
from language_models.api.base import ApiModel

from language_models.model_message import MessageMetadata, ModelMessage
from language_models.tools.base_tool import BaseTool


class DateAndTimeTool(BaseTool):
    def __init__(self):
        super().__init__(
            "get_date_and_time",
            "retrieve the current date and time",
            [],
        )

    def action(
        self,
        arguments: Dict[str, Any],
        model: ApiModel,
        messages: List[ModelMessage],
        metadata: MessageMetadata,
    ) -> str:
        return (
            "The current date and time is: "
            + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            + ". When answering questions about the current date or time, use this information, don't mention not being able to use the current time and/or date."
        )

    def get_example_messages(self) -> List[ModelMessage]:
        return []
