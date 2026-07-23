from __future__ import annotations

import hashlib
import math
import re
from functools import lru_cache
from collections import Counter
from typing import List

from langchain_core.embeddings import Embeddings
from app.config import settings


class SentenceTransformerEmbeddings(Embeddings):
    """基于 sentence-transformers 的本地嵌入模型。"""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = None

    def _get_model(self):
        if self.model is not None:
            return self.model

        try:
            from sentence_transformers import SentenceTransformer
        except Exception as error:
            print(f"sentence-transformers 不可用，回退到哈希嵌入: {error}")
            self.model = HashEmbeddings()
            return self.model

        try:
            self.model = SentenceTransformer(
                self.model_name,
                cache_folder=str(settings.model_cache_dir),
            )
        except Exception as error:
            print(f"加载本地嵌入模型失败，回退到哈希嵌入: {error}")
            self.model = HashEmbeddings()

        return self.model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        model = self._get_model()
        if isinstance(model, HashEmbeddings):
            return model.embed_documents(texts)

        vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return vectors.tolist()

    def embed_query(self, text: str) -> List[float]:
        model = self._get_model()
        if isinstance(model, HashEmbeddings):
            return model.embed_query(text)

        vector = model.encode([text], normalize_embeddings=True, show_progress_bar=False)
        return vector[0].tolist()


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


@lru_cache(maxsize=1)
def get_embeddings() -> Embeddings:
    """根据配置创建嵌入模型，失败时回退到哈希向量。"""
    if settings.embedding_provider == "sentence_transformers":
        return SentenceTransformerEmbeddings(settings.embedding_model_name)

    return HashEmbeddings()
