from typing import Any, Sequence


class EmbeddingModel:
    def __init__(self, dimensions: int):
        self.model = None
        self.dimensions = dimensions

    def embed_document(self, document: str) -> Any:
        raise NotImplementedError("Subclasses must implement this method")

    def embed_documents(self, documents: Sequence[str]) -> Any:
        raise NotImplementedError("Subclasses must implement this method")

    def embed_query(self, query: str) -> Any:
        raise NotImplementedError("Subclasses must implement this method")
