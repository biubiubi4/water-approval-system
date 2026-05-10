from __future__ import annotations

from typing import Any, Dict, List

from app.vector_store import vector_store


REQUIRED_FIELDS = ["applicant_name", "applicant_id", "project_name", "water_use", "attachments"]


def knowledge_search(query: str, top_k: int = 4) -> List[Dict[str, Any]]:
    results = vector_store.similarity_search_with_score(query, k=top_k)
    payload: List[Dict[str, Any]] = []
    for document, score in results:
        payload.append(
            {
                "content": document.page_content,
                "metadata": document.metadata,
                "score": float(score),
            }
        )
    return payload


def check_completeness(application: Dict[str, Any]) -> Dict[str, Any]:
    missing = [field for field in REQUIRED_FIELDS if not application.get(field)]
    attachments = application.get("attachments") or []
    issues: List[str] = []

    if missing:
        issues.extend(f"缺少字段: {field}" for field in missing)

    if not isinstance(attachments, list):
        issues.append("attachments 必须是文件列表")

    if isinstance(attachments, list) and not attachments:
        issues.append("未上传任何附件")

    return {
        "complete": len(issues) == 0,
        "missing_fields": missing,
        "issues": issues,
    }