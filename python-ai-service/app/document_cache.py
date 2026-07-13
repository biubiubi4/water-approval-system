from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from langchain.schema import Document
except ImportError:
    from langchain_core.documents import Document

from app.config import settings


CACHE_VERSION = 1


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def calculate_file_hash(file_path: Path) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _cache_dir() -> Path:
    return Path(settings.document_cache_dir)


def _cache_path(file_hash: str) -> Path:
    return _cache_dir() / f"{file_hash}.json"


def _document_reader(documents: List[Document], file_path: Path) -> str:
    for document in documents:
        reader = (document.metadata or {}).get("reader")
        if reader:
            return str(reader)
    return file_path.suffix.lower().lstrip(".") or "generic"


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    return str(value)


def _file_stat_payload(file_path: Path, file_hash: str) -> Dict[str, Any]:
    stat = file_path.stat()
    return {
        "file_path": str(file_path),
        "file_name": file_path.name,
        "file_hash": file_hash,
        "file_size": stat.st_size,
        "file_mtime": stat.st_mtime,
    }


def load_cached_documents(file_path: Path) -> Optional[List[Document]]:
    if not settings.document_cache_enabled:
        return None

    try:
        file_hash = calculate_file_hash(file_path)
        cache_path = _cache_path(file_hash)
        if not cache_path.exists():
            print(f"[附件解析] 缓存未命中: {file_path.name}")
            return None

        with cache_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        if payload.get("cache_version") != CACHE_VERSION or payload.get("file_hash") != file_hash:
            print(f"[附件解析] 缓存版本或哈希不匹配，重新解析: {file_path.name}")
            return None

        documents: List[Document] = []
        for item in payload.get("documents", []):
            text = str(item.get("page_content") or "")
            if not text.strip():
                continue

            metadata = dict(item.get("metadata") or {})
            metadata.update(
                {
                    "source": metadata.get("source") or file_path.name,
                    "file_path": str(file_path),
                    "reader": metadata.get("reader") or payload.get("reader"),
                    "document_cache_hit": True,
                    "document_cache_key": file_hash,
                    "document_cache_path": str(cache_path),
                    "document_cache_updated_at": payload.get("updated_at"),
                }
            )
            documents.append(Document(page_content=text, metadata=metadata))

        if documents:
            print(f"[附件解析] 缓存命中: {file_path.name}, chunks={len(documents)}")
            return documents

        print(f"[附件解析] 缓存内容为空，重新解析: {file_path.name}")
        return None
    except Exception as error:
        print(f"[附件解析] 读取缓存失败 {file_path.name}: {error}")
        return None


def write_cached_documents(file_path: Path, documents: List[Document]) -> None:
    if not settings.document_cache_enabled or not documents:
        return

    try:
        file_hash = calculate_file_hash(file_path)
        cache_dir = _cache_dir()
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = _cache_path(file_hash)

        existing_created_at = None
        if cache_path.exists():
            try:
                with cache_path.open("r", encoding="utf-8") as file:
                    existing_created_at = json.load(file).get("created_at")
            except Exception:
                existing_created_at = None

        payload = {
            "cache_version": CACHE_VERSION,
            **_file_stat_payload(file_path, file_hash),
            "reader": _document_reader(documents, file_path),
            "pages": sorted(
                {
                    str((document.metadata or {}).get("page"))
                    for document in documents
                    if (document.metadata or {}).get("page") is not None
                }
            ),
            "chunks": len(documents),
            "created_at": existing_created_at or _now_iso(),
            "updated_at": _now_iso(),
            "documents": [
                {
                    "page_content": document.page_content,
                    "metadata": {
                        key: _json_safe(value)
                        for key, value in dict(document.metadata or {}).items()
                        if key not in {"document_cache_hit", "document_cache_path", "document_cache_updated_at"}
                    },
                }
                for document in documents
                if str(document.page_content or "").strip()
            ],
        }

        temp_path = cache_path.with_suffix(".tmp")
        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
        temp_path.replace(cache_path)
        print(f"[附件解析] 已写入缓存: {file_path.name}, chunks={len(documents)}")
    except Exception as error:
        print(f"[附件解析] 写入缓存失败 {file_path.name}: {error}")


def mark_cache_miss(file_path: Path, documents: List[Document]) -> List[Document]:
    if not settings.document_cache_enabled:
        return documents

    try:
        file_hash = calculate_file_hash(file_path)
    except Exception:
        file_hash = ""

    for document in documents:
        metadata = dict(document.metadata or {})
        metadata["document_cache_hit"] = False
        if file_hash:
            metadata["document_cache_key"] = file_hash
        document.metadata = metadata
    return documents
