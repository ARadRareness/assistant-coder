from enum import Enum


class Role(Enum):
    SYSTEM = 1
    USER = 2
    ASSISTANT = 3


class MessageMetadata:
    def __init__(self, timestamp, selected_files, ask_permission_to_run_tools=False):
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

    def get_message(self, use_metadata=False):
        if self.is_user_message() and use_metadata:
            return f"{self.get_metadata_info()}{self.get_content()}"
        else:
            return self.get_content()

    def get_metadata_info(self):
        info = ""

        if self.metadata.selected_files:
            files = ['"' + file + '"' for file in self.metadata.selected_files]

            numbered_list = []
            for i, file in enumerate(files):
                numbered_list.append(f"{i+1}. {file}")

            info += f"The currently selected files are {', '.join(numbered_list)}. "

        if info:
            info = f"[Metadata info provided with the message, don't write it out unless necessary: {info.strip()}] "
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
