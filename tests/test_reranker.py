import unittest
from language_models.reranker import Reranker
from sentence_transformers import util  # type: ignore


class TestSentenceTransformersReranker(unittest.TestCase):
    def setUp(self):
        # Initialize the model
        self.model = Reranker()

    def test_document_ranking(self):
        query = "What is my password?"
        documents = [
            "The secret code is 4512.",
            "Step by step cake baking instructions.",
            "History of cakes and baking.",
            "Best practices for web development.",
        ]

        # Embed the query and documents
        reranked_results = self.model.rerank_documents(query, documents)

        self.assertEqual(reranked_results[0][0], documents[0])


if __name__ == "__main__":
    unittest.main()
