from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from typing import List

from langchain_core.embeddings import Embeddings


class HashEmbeddings(Embeddings):
    """A deterministic local embedding implementation for offline development."""

    def __init__(self, dimension: int = 256):
        self.dimension = dimension

    def _tokenize(self, text: str) -> List[str]:
        tokens = re.findall(r"[\u4e00-\u9fffA-Za-z0-9_]+", text.lower())
        return tokens or [text.lower()]

    def _embed(self, text: str) -> List[float]:
        vector = [0.0] * self.dimension
        counts = Counter(self._tokenize(text))
        for token, count in counts.items():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            weight = 1.0 + math.log(1.0 + count)
            vector[index] += weight

        norm = math.sqrt(sum(value * value for value in vector))
        if norm > 0:
            vector = [value / norm for value in vector]
        return vector

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)