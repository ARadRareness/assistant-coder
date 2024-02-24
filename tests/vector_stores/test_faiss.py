import unittest

from language_models.embedding_models.angle_embedding_model import AngleEmbeddingModel
from language_models.vector_stores.faiss import FAISS


class test_faiss(unittest.TestCase):
    def test_faiss_add_documents(self):
        embedding_model = AngleEmbeddingModel()

        documents = (
            "This is a recipe",
            "This is a test document",
            "This is a test movie",
            "This is a test song",
            "This is a test book",
        )

        faiss = FAISS(embedding_model)
        faiss.add_documents(documents)

        retrieve_count = 3

        retrieved_documents = faiss.search("Get me the test document", retrieve_count)

        self.assertEqual(len(retrieved_documents), retrieve_count)

        if retrieved_documents:
            self.assertEqual(retrieved_documents[0], documents[1])
