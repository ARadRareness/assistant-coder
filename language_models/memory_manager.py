import os
from language_models.embedding_models.angle_embedding_model import AngleEmbeddingModel
from language_models.vector_stores.faiss import FAISS


class MemoryManager:
    def __init__(self):
        self.embedding_model = AngleEmbeddingModel()
        self.vector_store = FAISS(self.embedding_model)
        self.load_all_documents()

    def load_all_documents(self):
        if os.path.exists("knowledge_base"):
            for file in os.listdir("knowledge_base"):
                with open(f"knowledge_base/{file}", "r", encoding="utf8") as f:
                    content = f.read()

                    if content:
                        self.vector_store.add_document(content)

    def add_document(self, document):
        self.vector_store.add_document(document)

    def get_most_relevant_documents(self, query, number_of_documents):
        return self.vector_store.search(query, number_of_documents)
