import faiss

from language_models.embedding_models.base import EmbeddingModel


class FAISS:
    def __init__(self, embedding_model: EmbeddingModel):
        self.index = faiss.IndexFlatL2(embedding_model.dimensions)
        self.documents = []
        self.embedding_model = embedding_model

    def add_document(self, document):
        self.index.add(self.embedding_model.embed_document(document))
        self.documents.append(document)

    def add_documents(self, documents):
        self.index.add(self.embedding_model.embed_documents(documents))
        self.documents.extend(documents)

    def search(self, query, k):
        query_vector = self.embedding_model.embed_query(query)

        d, i = self.index.search(query_vector, k)

        return tuple(self.documents[num] for num in i[0])
