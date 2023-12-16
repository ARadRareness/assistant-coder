class ModelResponse:
    def __init__(self, text: str, model: str):
        self.text = text
        self.model = model

    def get_text(self):
        return self.text

    def get_model(self):
        return self.model
