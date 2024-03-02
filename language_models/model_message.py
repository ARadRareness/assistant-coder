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
        clipboard_content: str = "",
    ):
        self.timestamp = timestamp
        self.selected_files = selected_files
        self.ask_permission_to_run_tools = ask_permission_to_run_tools
        self.clipboard_content = clipboard_content
        self.tool_output = ""
        self.knowledge_information = ""
        self.reflection_text = ""

    def set_knowledge_information(self, knowledge_information: str) -> None:
        self.knowledge_information = knowledge_information

    def set_reflection_text(self, reflection_text: str) -> None:
        self.reflection_text = reflection_text

    def set_tool_output(self, tool_output: str) -> None:
        self.tool_output = tool_output


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

    def append_content(self, appended_content: str) -> None:
        self.content += f"\n\n{appended_content}"

    def get_content(self) -> str:
        return self.content

    def get_message(self, use_metadata: bool = False) -> str:
        if self.is_user_message() and use_metadata:
            return f"{self.get_prefix_metadata_info()}{self.get_content()}{self.get_suffix_metadata_info()}"
        else:
            return self.get_content()

    def get_prefix_metadata_info(self) -> str:
        info = ""

        if self.metadata.knowledge_information:
            info = (
                "(Your knowledge base contains the following information: "
                + self.metadata.knowledge_information
                + ")\n\n"
            )

        combined_info = ""

        if self.metadata.clipboard_content:
            combined_info += f'The clipboard contains the following text: "{self.metadata.clipboard_content}". '

        if self.metadata.selected_files:
            files = ['"' + file + '"' for file in self.metadata.selected_files]

            numbered_list: List[str] = []
            for i, file in enumerate(files):
                numbered_list.append(f"{i+1}. {file}")

            combined_info += (
                f"The currently selected files are {', '.join(numbered_list)}. "
            )

        if self.metadata.reflection_text:
            combined_info += f"You have previously concerning the current topic had the following reflections: {self.metadata.reflection_text}. "

        if combined_info:
            info += f"[Metadata info provided with the message, don't write it out unless necessary: {combined_info.strip()}] "

        return info

    def get_suffix_metadata_info(self) -> str:
        info_list: List[str] = []

        if self.metadata.tool_output:
            info_list.append(self.metadata.tool_output)

        if info_list:
            output: str = "\n".join(info_list)
            return f"\n(Information to the model, {output})"
        return ""

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
