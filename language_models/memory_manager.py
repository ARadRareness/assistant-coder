import os
from typing import Generator, List, Optional, Sequence, Tuple
from language_models.embedding_models.angle_embedding_model import AngleEmbeddingModel
from language_models.embedding_models.base import EmbeddingModel
from language_models.reranker import Reranker
from language_models.vector_stores.faiss import FAISS


class MemoryManager:
    embedding_model: Optional[EmbeddingModel] = None
    reranker: Optional[Reranker] = None

    def __init__(self, knowledge_base_path: str):
        self.vector_store: Optional[FAISS] = None
        self.knowledge_base_path = knowledge_base_path

    def get_most_relevant_documents(
        self, query: str, number_of_documents: int
    ) -> Tuple[str] | Tuple[()]:
        if not self.vector_store:
            return ()
        return self.vector_store.search(query, number_of_documents)

    def get_most_relevant_documents_with_rerank(
        self, query: str, number_of_documents: int
    ) -> List[str]:
        if not MemoryManager.reranker:
            MemoryManager.reranker = Reranker()

        relevant_documents = self.get_most_relevant_documents(
            query, number_of_documents * 3
        )
        results = MemoryManager.reranker.rerank_documents(query, relevant_documents)

        return list(result[0] for result in results[:number_of_documents])

    def refresh_memory(self) -> None:
        if not self.vector_store:
            if not MemoryManager.embedding_model:
                MemoryManager.embedding_model = AngleEmbeddingModel()
            self.vector_store = FAISS(MemoryManager.embedding_model)

        reload_documents = False

        for document in self._read_knowledge_base():
            if not self.vector_store.has_document(document):
                reload_documents = True
                break

        if reload_documents:
            if not MemoryManager.embedding_model:
                MemoryManager.embedding_model = AngleEmbeddingModel()
            self.vector_store = FAISS(MemoryManager.embedding_model)
            self._load_all_documents(list(self._read_knowledge_base()))

    def _load_all_documents(self, documents: Sequence[str]) -> None:
        if not self.vector_store:
            return
        for document in documents:
            self.vector_store.add_document(document)

    def _read_knowledge_base(self) -> Generator[str, None, None]:
        if os.path.exists(self.knowledge_base_path):
            for file in os.listdir(self.knowledge_base_path):
                with open(
                    os.path.join(self.knowledge_base_path, file), "r", encoding="utf8"
                ) as f:
                    content = f.read()

                    if content:
                        yield content
