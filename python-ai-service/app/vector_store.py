from __future__ import annotations

import shutil
import uuid
from pathlib import Path

try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma

from app.config import settings
from app.embeddings import get_embeddings


_BASE_COLLECTION_NAME = settings.default_collection


_CORRUPTION_MARKERS = (
    "Error loading hnsw index",
    "Error constructing hnsw segment reader",
    "Error creating hnsw segment reader",
    "Error sending backfill request to compactor",
)


def _is_corrupted_index(error: Exception) -> bool:
    message = str(error)
    return any(marker in message for marker in _CORRUPTION_MARKERS)


def _clear_persist_directory() -> None:
    persist_dir = Path(settings.chroma_dir)
    if persist_dir.exists():
        shutil.rmtree(persist_dir, ignore_errors=True)


def init_vector_store() -> Chroma:
    """初始化向量存储"""
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    try:
        return Chroma(
            collection_name=settings.default_collection,
            embedding_function=get_embeddings(),
            persist_directory=str(settings.chroma_dir),
        )
    except Exception as error:
        if not _is_corrupted_index(error):
            raise

        print(f"检测到损坏的向量库索引，清理后重建: {error}")
        _clear_persist_directory()
        settings.chroma_dir.mkdir(parents=True, exist_ok=True)
        return Chroma(
            collection_name=settings.default_collection,
            embedding_function=get_embeddings(),
            persist_directory=str(settings.chroma_dir),
        )


vector_store = init_vector_store()


def rebuild_vector_store() -> Chroma:
    """清理持久化目录并重建当前集合实例。"""
    settings.default_collection = _BASE_COLLECTION_NAME
    _clear_persist_directory()
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    new_store = init_vector_store()
    vector_store.__dict__.clear()
    vector_store.__dict__.update(new_store.__dict__)
    return vector_store
