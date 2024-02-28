from typing import List, Tuple, Sequence
from sentence_transformers import CrossEncoder  # type: ignore


class Reranker:
    def __init__(self):
        self.model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    def rerank_documents(
        self,
        query: str,
        documents: Sequence[str],
    ) -> List[Tuple[str, float]]:
        candidates = list(((query, document)) for document in documents)
        scores = self.model.predict(candidates)  # type: ignore
        return list(zip(documents, scores))  # type: ignore
