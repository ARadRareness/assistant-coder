import os
from typing import Generator, List, Optional, Sequence, Tuple
from language_models.embedding_models.angle_embedding_model import AngleEmbeddingModel
from language_models.embedding_models.base import EmbeddingModel
from language_models.reranker import Reranker
from language_models.vector_stores.faiss import FAISS


class MemoryManager:
    def __init__(self):
        self.embedding_model: Optional[EmbeddingModel] = None
        self.vector_store: Optional[FAISS] = None
        self.reranker: Optional[Reranker] = None

    def get_most_relevant_documents(
        self, query: str, number_of_documents: int
    ) -> Tuple[str] | Tuple[()]:
        if not self.vector_store:
            return ()
        return self.vector_store.search(query, number_of_documents)

    def get_most_relevant_documents_with_rerank(
        self, query: str, number_of_documents: int
    ) -> List[str]:
        if not self.reranker:
            self.reranker = Reranker()

        relevant_documents = self.get_most_relevant_documents(
            query, number_of_documents * 3
        )
        results = self.reranker.rerank_documents(query, relevant_documents)

        return list(result[0] for result in results[:number_of_documents])

    def refresh_memory(self) -> None:
        if not self.vector_store:
            self.embedding_model = AngleEmbeddingModel()
            self.vector_store = FAISS(self.embedding_model)

        reload_documents = False

        for document in self._read_knowledge_base():
            if not self.vector_store.has_document(document):
                reload_documents = True
                break

        if reload_documents:
            if not self.embedding_model:
                self.embedding_model = AngleEmbeddingModel()
            self.vector_store = FAISS(self.embedding_model)
            self._load_all_documents(list(self._read_knowledge_base()))

    def _load_all_documents(self, documents: Sequence[str]) -> None:
        if not self.vector_store:
            return
        for document in documents:
            self.vector_store.add_document(document)

    def _read_knowledge_base(self) -> Generator[str, None, None]:
        if os.path.exists("knowledge_base"):
            for file in os.listdir("knowledge_base"):
                with open(f"knowledge_base/{file}", "r", encoding="utf8") as f:
                    content = f.read()

                    if content:
                        yield content
