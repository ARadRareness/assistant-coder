from language_models.api.base import Model
from language_models.model_message import ModelMessage, Role


class ModelConversation:
    def __init__(self, single_message_mode=False):
        self.messages = []
        self.single_message_mode = single_message_mode

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

        return self.messages

    def add_user_message(self, content: str):
        self.messages.append(ModelMessage(Role.USER, content))

    def add_system_message(self, content: str):
        self.messages.append(ModelMessage(Role.SYSTEM, content))

    def generate_message(
        self, model: Model, max_tokens: int, single_message_mode: bool
    ):
        messages = self.get_messages(single_message_mode)

        response = model.generate_text(messages, max_tokens)
        self.messages.append(ModelMessage(Role.ASSISTANT, response.get_text()))

        return response.get_text()
