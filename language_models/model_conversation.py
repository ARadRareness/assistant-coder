import datetime
from typing import List

from language_models.api.base import Model
from language_models.model_message import MessageMetadata, ModelMessage, Role
from language_models.tool_manager import ToolManager


class ModelConversation:
    def __init__(self, single_message_mode=False):
        self.messages = []
        self.single_message_mode = single_message_mode
        self.tool_manager = ToolManager()

    def get_messages(self, single_message_mode=False):
        if not self.messages:
            return []

        if single_message_mode:
            messages = []
            system_message = None
            for message in self.messages:
                if message.is_system_message():
                    system_message = message

            if system_message:
                messages.append(system_message)

            if len(self.messages) > 0 and not system_message == self.messages[-1]:
                messages.append(self.messages[-1])

            return messages

        return self.messages[::]

    def add_user_message(self, content: str, metadata: MessageMetadata):
        self.messages.append(ModelMessage(Role.USER, content, metadata))

    def add_system_message(self, content: str, metadata: MessageMetadata):
        full_content = (
            "Each user message contains some metadata, a timestamp and optionally a list of checked files.\n"
            + content,
        )
        self.messages.append(ModelMessage(Role.SYSTEM, full_content, metadata))

    def generate_message(
        self,
        model: Model,
        max_tokens: int,
        single_message_mode: bool,
        use_metadata: bool = False,
        use_tools: bool = False,
        use_reflections: bool = False,
    ):
        messages = self.get_messages(single_message_mode)

        metadata = generate_metadata()

        if use_reflections and messages and messages[-1].is_user_message():
            self.handle_reflections(
                model, max_tokens, messages, use_metadata=use_metadata
            )

        if use_tools and messages:
            self.handle_tool_use(model, max_tokens, messages, use_metadata=use_metadata)

        response = model.generate_text(messages, max_tokens, use_metadata=use_metadata)

        self.messages.append(
            ModelMessage(Role.ASSISTANT, response.get_text(), metadata)
        )

        return response.get_text()

    def handle_reflections(
        self,
        model: Model,
        max_tokens: int,
        messages: list[ModelMessage],
        use_metadata: bool = False,
    ):
        last_message = messages.pop(-1)

        messages.append(
            ModelMessage(
                Role.REFLECTION,
                "Reflect on the user message below, go step by step through your thoughts how to best fulfill the request of the message.\nMESSAGE: "
                + last_message.get_message(use_metadata=use_metadata),
                last_message.get_metadata(),
            )
        )

        response = model.generate_text(messages, max_tokens, use_metadata=use_metadata)
        messages[-1] = last_message  # Restore the old user message

        reflection_message = ModelMessage(
            Role.REFLECTION, response.get_text(), last_message.get_metadata()
        )
        messages.append(reflection_message)
        self.messages.append(reflection_message)

    def handle_tool_use(
        self,
        model: Model,
        max_tokens: int,
        messages: list[ModelMessage],
        use_metadata: bool = False,
    ):
        last_message = messages[-1]
        tool_messages = self.tool_manager.get_tool_conversation(last_message)
        response = model.generate_text(
            tool_messages, max_tokens=max_tokens, use_metadata=use_metadata
        )
        output = self.tool_manager.parse_and_execute(response)

        if output:
            messages.append(
                ModelMessage(Role.TOOL_OUTPUT, output, last_message.get_metadata())
            )


def generate_metadata():
    return MessageMetadata(datetime.datetime.now(), [])
