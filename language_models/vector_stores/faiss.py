import hashlib
from typing import List, Sequence, Set, Tuple
import faiss  # type: ignore

from language_models.embedding_models.base import EmbeddingModel


class FAISS:
    def __init__(self, embedding_model: EmbeddingModel):
        self.index = faiss.IndexFlatL2(embedding_model.dimensions)
        self.documents: List[str] = []
        self.documents_checksums: Set[str] = set()
        self.embedding_model = embedding_model

    def add_document(self, document: str) -> None:
        self.index.add(self.embedding_model.embed_document(document))  # type: ignore
        self.documents.append(document)
        self.documents_checksums.add(self.md5sum(document))

    def add_documents(self, documents: Sequence[str]) -> None:
        self.index.add(self.embedding_model.embed_documents(documents))  # type: ignore
        self.documents.extend(documents)
        self.documents_checksums.update(map(self.md5sum, documents))

    def search(self, query: str, k: int) -> Tuple[str] | Tuple[()]:
        query_vector = self.embedding_model.embed_query(query)

        _, i = self.index.search(query_vector, k)  # type: ignore

        filtered_results: List[int] = filter(lambda x: x != -1, i[0])  # type: ignore

        return tuple(list(self.documents[num] for num in filtered_results))

    def has_document(self, document: str):
        return self.md5sum(document) in self.documents_checksums

    def md5sum(self, document: str):
        return hashlib.md5(document.encode()).hexdigest()
