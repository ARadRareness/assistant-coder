import datetime
import os
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Optional, Tuple
from language_models.api.base import ApiModel
from language_models.model_message import MessageMetadata, ModelMessage, Role


class BaseTool:
    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        available_arguments: Optional[List[Tuple[str, str]]] = None,
        ask_permission_to_run: bool = False,
    ):
        if name is None:
            raise ValueError("name must be provided")
        if description is None:
            raise ValueError("description must be provided")
        if available_arguments is None:
            raise ValueError("available_arguments must be provided")

        self.name = name
        self.description = description
        self.available_arguments = available_arguments

        self.example_path = "C:\\test.txt"
        self.ask_permission_to_run = ask_permission_to_run

    def action(
        self,
        arguments: Dict[str, Any],
        model: ApiModel,
        messages: List[ModelMessage],
        metadata: MessageMetadata,
    ) -> str:
        raise NotImplementedError("Subclasses must implement this method")

    def ask_permission_message(
        self, arguments: Dict[str, Any], metadata: MessageMetadata
    ) -> Optional[str]:
        if self.ask_permission_to_run:
            return "Do you want to run this tool?"
        else:
            return None

    def get_available_arguments(self) -> Optional[List[Tuple[str, str]]]:
        return self.available_arguments

    def get_example_messages(self) -> List[ModelMessage]:
        raise NotImplementedError("Subclasses must implement this method")

    def __str__(self) -> str:
        return self.__class__.__name__

    def get_example_dialogue(
        self, user_message: str, assistant_message: str
    ) -> List[ModelMessage]:
        return [
            ModelMessage(
                Role.USER,
                user_message,
                MessageMetadata(datetime.datetime.now(), [self.example_path]),
            ),
            ModelMessage(
                Role.ASSISTANT,
                assistant_message,
                MessageMetadata(datetime.datetime.now(), [self.example_path]),
            ),
        ]

    def get_user_permission(self, message: str) -> bool:
        with tempfile.NamedTemporaryFile(mode="w+t", delete=False) as temp_file:
            temp_file_name = temp_file.name
            temp_file.write(message)
            temp_file.flush()  # Ensure all data is written to the file

        try:
            result = subprocess.call(
                [
                    sys.executable,
                    "language_models/helpers/permission_notifier.py",
                    temp_file.name,
                ]
            )
            return result == 0
        finally:
            os.remove(temp_file_name)
