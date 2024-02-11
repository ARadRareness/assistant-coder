from language_models.model_message import MessageMetadata


class BaseTool:
    def __init__(self, name, description, arguments):
        self.name = name
        self.description = description
        self.arguments = arguments

    def action(self, arguments, metadata: MessageMetadata):
        raise NotImplementedError("Subclasses must implement this method")

    def __str__(self):
        return self.__class__.__name__
