from enum import Enum


class Role(Enum):
    SYSTEM = 1
    USER = 2
    ASSISTANT = 3


class MessageMetadata:
    def __init__(self, timestamp, selected_files):
        self.timestamp = timestamp
        self.selected_files = selected_files


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

    def get_content(self):
        return self.content

    def get_full_message(self):
        return f"{self.get_metadata_info()}{self.get_content()}"

    def get_metadata_info(self):
        info = ""

        if self.metadata.timestamp:
            info += f"The current time is {self.metadata.timestamp:%d %b %Y %H:%M}, which is a {self.metadata.timestamp:%A}."

        if self.metadata.selected_files:
            files = ['"' + file + '"' for file in self.metadata.selected_files]
            info += f"The currently selected files are {', '.join(files)}."

        if info:
            info = f"({info}) "

        return info

    def get_role(self):
        return self.role.name.lower()

    def get_metadata(self):
        return self.metadata

    def get_actor_name(self):
        return self.actor_name

    def is_system_message(self):
        return self.role == Role.SYSTEM

    def is_user_message(self):
        return self.role == Role.USER

    def is_assistant_message(self):
        return self.role == Role.ASSISTANT
