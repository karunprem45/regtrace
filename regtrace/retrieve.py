"""Split summary pages into chunks that remember where they came from, then search them."""
from dataclasses import dataclass

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class Chunk:
    chunk_id: str      # e.g. "K193456:p2:c1"
    k_number: str
    page: int
    text: str


def chunk_pages(k_number: str, pages: list[str], max_words: int = 120, overlap: int = 20) -> list[Chunk]:
    out = []
    step = max_words - overlap
    for p, text in enumerate(pages, start=1):
        words = text.split()
        for c, start in enumerate(range(0, max(len(words), 1), step)):
            piece = " ".join(words[start:start + max_words])
            if piece:
                out.append(Chunk(f"{k_number}:p{p}:c{c}", k_number, p, piece))
            if start + max_words >= len(words):
                break
    return out


class Retriever:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.matrix = self.vec.fit_transform([c.text for c in chunks]) if chunks else None

    def search(self, query: str, k: int = 5) -> list[tuple[Chunk, float]]:
        if self.matrix is None:
            return []
        scores = cosine_similarity(self.vec.transform([query]), self.matrix)[0]
        order = scores.argsort()[::-1][:k]
        return [(self.chunks[i], float(scores[i])) for i in order if scores[i] > 0]
