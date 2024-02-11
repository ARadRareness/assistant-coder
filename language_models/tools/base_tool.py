import datetime
from language_models.model_message import MessageMetadata, ModelMessage, Role


class BaseTool:
    def __init__(self, name, description, arguments):
        self.name = name
        self.description = description
        self.arguments = arguments

        self.example_path = "C:\\test.txt"

    def action(self, arguments, metadata: MessageMetadata):
        raise NotImplementedError("Subclasses must implement this method")

    def get_example_messages(self):
        raise NotImplementedError("Subclasses must implement this method")

    def __str__(self):
        return self.__class__.__name__

    def get_example_dialogue(self, user_message, assistant_message):
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
