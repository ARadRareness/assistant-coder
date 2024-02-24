import unittest

from language_models.embedding_models.angle_embedding_model import AngleEmbeddingModel
import sentence_transformers  # type: ignore


class TestAngleEmbeddingModel(unittest.TestCase):

    def test_embeddings(self):

        embedding_model = AngleEmbeddingModel()
        vectors = embedding_model.embed_documents(
            ("This is a recipe", "This is a test document", "This is a test movie")
        )
        vectorQuery = embedding_model.embed_query("Get me the test document")

        # Assert that the second document is the most similar to the query

        print(len(vectorQuery[0]))

        self.assertGreater(
            sentence_transformers.util.cos_sim(vectorQuery, vectors[1]),  # type: ignore
            sentence_transformers.util.cos_sim(vectorQuery, vectors[0]),  # type: ignore
        )

        self.assertGreater(
            sentence_transformers.util.cos_sim(vectorQuery, vectors[1]),  # type: ignore
            sentence_transformers.util.cos_sim(vectorQuery, vectors[2]),  # type: ignore
        )
