from __future__ import annotations

try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma

from app.config import settings
from app.embeddings import HashEmbeddings


def init_vector_store() -> Chroma:
    """初始化向量存储"""
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name=settings.default_collection,
        embedding_function=HashEmbeddings(),
        persist_directory=str(settings.chroma_dir),
    )


vector_store = init_vector_store()
