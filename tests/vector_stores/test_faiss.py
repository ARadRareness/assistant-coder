import unittest

from language_models.embedding_models.angle_embedding_model import AngleEmbeddingModel
from language_models.vector_stores.faiss import FAISS


class test_faiss(unittest.TestCase):
    def test_faiss(self):
        embedding_model = AngleEmbeddingModel()

        documents = (
            "This is a recipe",
            "This is a test document",
            "This is a test movie",
        )

        faiss = FAISS(embedding_model)
        faiss.add_documents(documents)

        retrieved_documents = faiss.search("Get me the test document", 3)

        self.assertEqual(retrieved_documents[0], documents[1])
