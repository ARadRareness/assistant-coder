import os
from language_models.embedding_models.angle_embedding_model import AngleEmbeddingModel
from language_models.vector_stores.faiss import FAISS


class MemoryManager:
    def __init__(self):
        self.embedding_model = None
        self.vector_store = None

    def get_most_relevant_documents(self, query, number_of_documents):
        if not self.vector_store:
            return []
        return self.vector_store.search(query, number_of_documents)

    def refresh_memory(self):
        if not self.vector_store:
            self.embedding_model = AngleEmbeddingModel()
            self.vector_store = FAISS(self.embedding_model)

        reload_documents = False

        for document in self._read_knowledge_base():
            if not self.vector_store.has_document(document):
                reload_documents = True
                break

        if reload_documents:
            self.vector_store = FAISS(self.embedding_model)
            self._load_all_documents(self._read_knowledge_base())

    def _load_all_documents(self, documents):
        for document in documents:
            self.vector_store.add_document(document)

    def _read_knowledge_base(self):
        if os.path.exists("knowledge_base"):
            for file in os.listdir("knowledge_base"):
                with open(f"knowledge_base/{file}", "r", encoding="utf8") as f:
                    content = f.read()

                    if content:
                        yield content
