import datetime
from typing import List

from language_models.api.base import Model
from language_models.model_message import MessageMetadata, ModelMessage, Role


class ModelConversation:
    def __init__(self, single_message_mode=False, reflection_mode=True):
        self.messages = []
        self.single_message_mode = single_message_mode
        self.reflection_mode = reflection_mode

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
            content
            + "\nEach user message contains some metadata, a timestamp and optionally a list of checked files,"
            + " you should only write it out when the request of the user requires it."
        )
        self.messages.append(ModelMessage(Role.SYSTEM, full_content, metadata))

    def generate_message(
        self, model: Model, max_tokens: int, single_message_mode: bool
    ):
        messages = self.get_messages(single_message_mode)

        metadata = generate_metadata()

        if self.reflection_mode and messages and messages[-1].is_user_message():
            last_message = messages.pop(-1)

            messages.append(
                ModelMessage(
                    Role.REFLECTION,
                    "Reflect on the user message below, go step by step through your thoughts how to best fulfill the request of the message.\nMESSAGE: "
                    + last_message.get_message(),
                    metadata,
                )
            )

            response = model.generate_text(messages, max_tokens)
            messages[-1] = last_message  # Restore the old user message

            reflection_message = ModelMessage(
                Role.REFLECTION, response.get_text(), metadata
            )
            messages.append(reflection_message)
            self.messages.append(reflection_message)

        response = model.generate_text(messages, max_tokens)

        self.messages.append(
            ModelMessage(Role.ASSISTANT, response.get_text(), metadata)
        )

        return response.get_text()


def generate_metadata():
    return MessageMetadata(datetime.datetime.now(), [])
