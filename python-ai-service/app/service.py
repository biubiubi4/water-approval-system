from __future__ import annotations

import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

try:
    from langchain.schema import Document
except ImportError:
    from langchain_core.documents import Document

from app.documents import process_documents, split_text
from app.vector_store import vector_store


def _collection():
    return vector_store._collection


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_metadata(metadata: Dict[str, Any] | None, source: str | None = None) -> Dict[str, Any]:
    payload = dict(metadata or {})
    if source:
        payload["source"] = source
    payload.setdefault("source", "manual")
    payload.setdefault("type", payload.get("type") or "manual")
    payload.setdefault("created_at", _now_iso())
    payload["updated_at"] = _now_iso()
    return payload


def _format_record(record_id: str, content: str | None, metadata: Dict[str, Any] | None) -> Dict[str, Any]:
    metadata = dict(metadata or {})
    content = content or ""
    return {
        "id": record_id,
        "content": content,
        "preview": content[:160],
        "source": metadata.get("source") or metadata.get("file_path") or "manual",
        "type": metadata.get("type") or "manual",
        "chunk": metadata.get("chunk"),
        "metadata": metadata,
        "created_at": metadata.get("created_at"),
        "updated_at": metadata.get("updated_at"),
    }


def _format_parsed_document(document: Document, record_id: str | None = None) -> Dict[str, Any]:
    metadata = dict(document.metadata or {})
    return {
        "id": record_id,
        "content": document.page_content,
        "preview": document.page_content[:200],
        "source": metadata.get("source") or metadata.get("file_path") or "manual",
        "file_path": metadata.get("file_path"),
        "document_name": metadata.get("document_name") or metadata.get("source"),
        "chunk_index": metadata.get("chunk_index") or metadata.get("chunk"),
        "page": metadata.get("page"),
        "metadata": metadata,
    }


def _load_records() -> List[Dict[str, Any]]:
    raw = _collection().get(include=["documents", "metadatas"])
    ids = raw.get("ids") or []
    documents = raw.get("documents") or []
    metadatas = raw.get("metadatas") or []

    records: List[Dict[str, Any]] = []
    for index, record_id in enumerate(ids):
        content = documents[index] if index < len(documents) else ""
        metadata = metadatas[index] if index < len(metadatas) else {}
        records.append(_format_record(record_id, content, metadata))
    return records


def _filter_records(
    query: str | None = None,
    source: str | None = None,
    record_type: str | None = None,
) -> List[Dict[str, Any]]:
    records = _load_records()

    if query:
        needle = query.lower().strip()
        records = [
            record
            for record in records
            if needle in record["content"].lower()
            or needle in record["source"].lower()
            or needle in record["type"].lower()
            or needle in str(record["metadata"]).lower()
        ]

    if source:
        needle = source.lower().strip()
        records = [record for record in records if needle in record["source"].lower()]

    if record_type:
        needle = record_type.lower().strip()
        records = [record for record in records if needle in record["type"].lower()]

    return records


def _build_summary(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    source_counter = Counter(record["source"] or "manual" for record in records)
    type_counter = Counter(record["type"] or "manual" for record in records)

    return {
        "total": len(records),
        "unique_sources": len(source_counter),
        "unique_types": len(type_counter),
        "sources": [{"name": name, "count": count} for name, count in source_counter.most_common()],
        "types": [{"name": name, "count": count} for name, count in type_counter.most_common()],
        "latest": records[:10],
    }


def _store_documents(documents: List[Document]) -> List[str]:
    if not documents:
        return []

    ids: List[str] = []
    texts: List[str] = []
    metadatas: List[Dict[str, Any]] = []

    for document in documents:
        record_id = str(uuid.uuid4())
        metadata = _normalize_metadata(document.metadata, document.metadata.get("source") if document.metadata else None)
        ids.append(record_id)
        texts.append(document.page_content)
        metadatas.append(metadata)

    vector_store.add_texts(texts=texts, metadatas=metadatas, ids=ids)
    return ids


def add_knowledge_files(paths: List[Path]) -> Dict[str, Any]:
    """添加文件到知识库"""
    if not paths:
        return {"status": "no files", "message": "没有提供文件"}

    failed_files: List[Dict[str, Any]] = []
    valid_paths: List[Path] = []
    for file_path in paths:
        if not file_path.exists():
            failed_files.append({"file": file_path.name, "reason": "文件不存在"})
            continue
        valid_paths.append(file_path)

    if not valid_paths:
        return {"status": "error", "message": "没有可解析的文件", "failed_files": failed_files}

    documents = process_documents(valid_paths)

    if not documents:
        return {
            "status": "error",
            "message": "未能从文件中提取内容",
            "failed_files": failed_files + [
                {"file": file_path.name, "reason": "文件内容为空、格式不受支持或缺少可提取文本"}
                for file_path in valid_paths
            ],
        }

    inserted_ids = _store_documents(documents)
    parsed_documents = [
        _format_parsed_document(document, inserted_ids[index] if index < len(inserted_ids) else None)
        for index, document in enumerate(documents)
    ]

    file_summaries: List[Dict[str, Any]] = []
    for file_path in paths:
        related_chunks = [item for item in parsed_documents if item.get("file_path") == str(file_path)]
        file_summaries.append(
            {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "chunk_count": len(related_chunks),
                "chunks": related_chunks,
            }
        )

    return {
        "status": "ok",
        "message": f"成功添加 {len(inserted_ids)} 条知识片段",
        "added": len(inserted_ids),
        "ids": inserted_ids,
        "files": [p.name for p in valid_paths],
        "failed_files": failed_files,
        "parsed_documents": parsed_documents,
        "file_summaries": file_summaries,
    }


def add_knowledge_text(
    text: str,
    source: str = "manual",
    metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """添加文本到知识库"""
    if not text.strip():
        return {"status": "error", "message": "文本内容不能为空"}

    chunks = split_text(text)
    payload = dict(metadata or {})
    payload["source"] = source

    documents: List[Document] = []
    for index, chunk in enumerate(chunks):
        documents.append(
            Document(
                page_content=chunk,
                metadata={
                    **payload,
                    "chunk": index + 1,
                },
            )
        )

    inserted_ids = _store_documents(documents)

    return {
        "status": "ok",
        "message": f"成功添加 {len(inserted_ids)} 条知识片段",
        "added": len(inserted_ids),
        "ids": inserted_ids,
    }


def list_knowledge_records(
    query: str | None = None,
    source: str | None = None,
    record_type: str | None = None,
) -> Dict[str, Any]:
    records = _filter_records(query=query, source=source, record_type=record_type)
    return {
        "records": records,
        "total": len(records),
        "summary": _build_summary(records),
    }


def get_knowledge_record(record_id: str) -> Dict[str, Any]:
    raw = _collection().get(ids=[record_id], include=["documents", "metadatas"])
    ids = raw.get("ids") or []
    if not ids:
        raise ValueError(f"未找到知识记录: {record_id}")

    document = (raw.get("documents") or [""])[0]
    metadata = (raw.get("metadatas") or [{}])[0]
    return _format_record(ids[0], document, metadata)


def create_knowledge_record(
    content: str,
    source: str = "manual",
    metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    if not content.strip():
        raise ValueError("内容不能为空")

    record_id = str(uuid.uuid4())
    payload = _normalize_metadata(metadata, source)
    vector_store.add_texts(texts=[content], metadatas=[payload], ids=[record_id])
    return _format_record(record_id, content, payload)


def update_knowledge_record(
    record_id: str,
    content: str,
    source: str = "manual",
    metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    existing = get_knowledge_record(record_id)
    if not content.strip():
        raise ValueError("内容不能为空")

    payload = dict(existing["metadata"])
    payload.update(metadata or {})
    payload["source"] = source or payload.get("source") or "manual"
    payload.setdefault("type", payload.get("type") or "manual")
    payload.setdefault("created_at", existing["created_at"])
    payload["updated_at"] = _now_iso()

    collection = _collection()
    collection.delete(ids=[record_id])
    vector_store.add_texts(texts=[content], metadatas=[payload], ids=[record_id])
    return _format_record(record_id, content, payload)


def delete_knowledge_record(record_id: str) -> Dict[str, Any]:
    existing = get_knowledge_record(record_id)
    _collection().delete(ids=[record_id])
    return {
        "status": "ok",
        "message": "记录已删除",
        "deleted": 1,
        "record": existing,
    }


def clear_knowledge() -> Dict[str, Any]:
    """清空知识库（谨慎使用）"""
    collection = _collection()
    count = collection.count()
    if count > 0:
        collection.delete()
    return {
        "status": "ok",
        "message": f"已清空 {count} 条知识",
        "cleared": count,
    }


def remove_knowledge_files(file_names: list[str]) -> Dict[str, Any]:
    """从向量库中移除指定来源（文件名）的知识片段"""
    if not file_names:
        return {"status": "no files", "message": "未提供文件名"}

    collection = _collection()
    removed = 0
    for name in file_names:
        try:
            collection.delete(where={"source": name})
            removed += 1
        except Exception as e:
            print(f"删除知识片段失败 ({name}): {e}")

    return {"status": "ok", "message": f"请求删除 {len(file_names)} 个来源，已尝试删除 {removed} 项", "requested": len(file_names), "removed": removed}
