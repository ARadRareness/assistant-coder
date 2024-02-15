import unittest

from language_models.embedders.angle_embedding_model import AngleEmbeddingModel
import sentence_transformers


class TestAngleEmbeddingModel(unittest.TestCase):

    def test_embeddings(self):

        embedder = AngleEmbeddingModel()
        vectors = embedder.embed_documents(
            ("This is a recipe", "This is a test document", "This is a test movie")
        )
        vectorQuery = embedder.embed_query("Get me the test document")

        # Assert that the second document is the most similar to the query

        self.assertGreater(
            sentence_transformers.util.cos_sim(vectorQuery, vectors[1]),
            sentence_transformers.util.cos_sim(vectorQuery, vectors[0]),
        )

        self.assertGreater(
            sentence_transformers.util.cos_sim(vectorQuery, vectors[1]),
            sentence_transformers.util.cos_sim(vectorQuery, vectors[2]),
        )
