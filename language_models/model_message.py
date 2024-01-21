from enum import Enum


class Role(Enum):
    SYSTEM = 1
    USER = 2
    ASSISTANT = 3
    REFLECTION = 4
    TOOL_OUTPUT = 5


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
        self.use_metadata = True

    def get_content(self):
        return self.content

    def get_message(self):
        if self.is_user_message() and self.use_metadata:
            return f"{self.get_metadata_info()}{self.get_content()}"
        else:
            return self.get_content()

    def get_metadata_info(self):
        info = ""

        if self.metadata.timestamp:
            info += f"The current time is {self.metadata.timestamp:%d %b %Y %H:%M}, {self.metadata.timestamp:%A}. "

        if self.metadata.selected_files:
            files = ['"' + file + '"' for file in self.metadata.selected_files]
            info += f"The currently selected files are {', '.join(files)}. "

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

    def is_reflection_message(self):
        return self.role == Role.REFLECTION

    def is_tool_output_message(self):
        return self.role == Role.TOOL_OUTPUT
