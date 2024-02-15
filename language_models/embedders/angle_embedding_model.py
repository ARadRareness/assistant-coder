from typing import List
from angle_emb import AnglE, Prompts


class AngleEmbeddingModel:
    def __init__(self):
        self.model = AnglE.from_pretrained(
            "WhereIsAI/UAE-Large-V1", pooling_strategy="cls"
        ).cuda()

    def embed_document(self, document: str):
        self.model.set_prompt(prompt=None)
        return self.model.encode(document, to_numpy=True)

    def embed_documents(self, documents: List[str]):
        self.model.set_prompt(prompt=None)
        return self.model.encode(documents, to_numpy=True)

    def embed_query(self, query: str):
        self.model.set_prompt(prompt=Prompts.C)
        return self.model.encode({"text": query}, to_numpy=True)
