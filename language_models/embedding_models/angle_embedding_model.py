from typing import Any, Sequence
from angle_emb import AnglE, Prompts  # type: ignore

from language_models.embedding_models.base import EmbeddingModel


class AngleEmbeddingModel(EmbeddingModel):
    def __init__(self):
        super().__init__(1024)
        self.model: AnglE = AnglE.from_pretrained(  # type: ignore
            "WhereIsAI/UAE-Large-V1", pooling_strategy="cls"
        ).cuda()

    def embed_document(self, document: str) -> Any:
        self.model.set_prompt(prompt=None)
        return self.model.encode(document, to_numpy=True)  # type: ignore

    def embed_documents(self, documents: Sequence[str]) -> Any:
        self.model.set_prompt(prompt=None)
        return self.model.encode(documents, to_numpy=True)  # type: ignore

    def embed_query(self, query: str) -> Any:
        self.model.set_prompt(prompt=Prompts.C)
        return self.model.encode({"text": query}, to_numpy=True)  # type: ignore
