from datetime import datetime
from enum import Enum
from typing import List, Sequence


class Role(Enum):
    SYSTEM = 1
    USER = 2
    ASSISTANT = 3


class MessageMetadata:
    def __init__(
        self,
        timestamp: datetime,
        selected_files: Sequence[str],
        ask_permission_to_run_tools: bool = False,
    ):
        self.timestamp = timestamp
        self.selected_files = selected_files
        self.ask_permission_to_run_tools = ask_permission_to_run_tools


class ModelMessage:
    def __init__(
        self,
        role: Role,
        content: str,
        metadata: MessageMetadata,
        actor_name: str = "default",
    ):
        self.role = role
        self.content = content
        self.metadata = metadata
        self.actor_name = actor_name

    def append_content(self, appended_content: str):
        self.content += f"\n\n{appended_content}"

    def get_content(self):
        return self.content

    def get_message(self, use_metadata: bool = False):
        if self.is_user_message() and use_metadata:
            return f"{self.get_metadata_info()}{self.get_content()}"
        else:
            return self.get_content()

    def get_metadata_info(self):
        info = ""

        if self.metadata.selected_files:
            files = ['"' + file + '"' for file in self.metadata.selected_files]

            numbered_list: List[str] = []
            for i, file in enumerate(files):
                numbered_list.append(f"{i+1}. {file}")

            info += f"The currently selected files are {', '.join(numbered_list)}. "

        if info:
            info = f"[Metadata info provided with the message, don't write it out unless necessary: {info.strip()}] "
        return info

    def get_role(self) -> str:
        return self.role.name.lower()

    def get_metadata(self) -> MessageMetadata:
        return self.metadata

    def get_actor_name(self) -> str:
        return self.actor_name

    def is_system_message(self) -> bool:
        return self.role == Role.SYSTEM

    def is_user_message(self) -> bool:
        return self.role == Role.USER

    def is_assistant_message(self) -> bool:
        return self.role == Role.ASSISTANT
