from typing import List


class EmbeddingModel:
    def __init__(self, dimensions: int):
        self.model = None
        self.dimensions = dimensions

    def embed_document(self, document: str):
        raise NotImplementedError("Subclasses must implement this method")

    def embed_documents(self, documents: List[str]):
        raise NotImplementedError("Subclasses must implement this method")

    def embed_query(self, query: str):
        raise NotImplementedError("Subclasses must implement this method")
