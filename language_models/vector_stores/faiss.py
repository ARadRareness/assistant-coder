import hashlib
import faiss

from language_models.embedding_models.base import EmbeddingModel


class FAISS:
    def __init__(self, embedding_model: EmbeddingModel):
        self.index = faiss.IndexFlatL2(embedding_model.dimensions)
        self.documents = []
        self.documents_checksums = set()
        self.embedding_model = embedding_model

    def add_document(self, document):
        self.index.add(self.embedding_model.embed_document(document))
        self.documents.append(document)
        self.documents_checksums.add(self.md5sum(document))

    def add_documents(self, documents):
        self.index.add(self.embedding_model.embed_documents(documents))
        self.documents.extend(documents)
        self.documents_checksums.update(map(self.md5sum, documents))

    def search(self, query, k):
        query_vector = self.embedding_model.embed_query(query)

        d, i = self.index.search(query_vector, k)

        return tuple(self.documents[num] for num in filter(lambda x: x != -1, i[0]))

    def has_document(self, document):
        return self.md5sum(document) in self.documents_checksums

    def md5sum(self, document):
        return hashlib.md5(document.encode()).hexdigest()
