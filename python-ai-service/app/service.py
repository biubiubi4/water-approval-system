from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

try:
    from langchain.schema import Document
except ImportError:
    from langchain_core.documents import Document

from app.vector_store import vector_store
from app.documents import process_documents, split_text


def add_knowledge_files(paths: List[Path]) -> Dict[str, Any]:
    """添加文件到知识库"""
    if not paths:
        return {"status": "no files", "message": "没有提供文件"}
    
    documents = process_documents(paths)
    
    if not documents:
        return {"status": "error", "message": "未能从文件中提取内容"}
    
    vector_store.add_documents(documents)
    
    return {
        "status": "ok",
        "message": f"成功添加 {len(documents)} 条知识片段",
        "added": len(documents),
        "files": [p.name for p in paths],
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
    metadata = metadata or {}
    metadata["source"] = source
    
    documents: List[Document] = []
    for i, chunk in enumerate(chunks):
        doc = Document(
            page_content=chunk,
            metadata={
                **metadata,
                "chunk": i + 1,
            }
        )
        documents.append(doc)
    
    vector_store.add_documents(documents)
    
    return {
        "status": "ok",
        "message": f"成功添加 {len(documents)} 条知识片段",
        "added": len(documents),
    }


def clear_knowledge() -> Dict[str, Any]:
    """清空知识库（谨慎使用）"""
    collection = vector_store._collection
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

    collection = vector_store._collection
    removed = 0
    for name in file_names:
        try:
            # 使用 metadata 中的 source 字段进行删除
            collection.delete(where={"source": name})
            removed += 1
        except Exception as e:
            print(f"删除知识片段失败 ({name}): {e}")

    return {"status": "ok", "message": f"请求删除 {len(file_names)} 个来源，已尝试删除 {removed} 项", "requested": len(file_names), "removed": removed}
