from __future__ import annotations

from typing import Any, Dict, List

from app.vector_store import vector_store


REQUIRED_FIELDS = ["applicant_name", "applicant_id", "project_name", "water_use", "attachments"]


CHECKLIST = [
    {
        "name": "取水许可申请书",
        "aliases": ["申请书", "取水申请书", "申请表", "water application form"],
    },
    {
        "name": "申请人身份证明或主体资格材料",
        "aliases": ["身份证", "身份证明", "营业执照", "主体资格", "法人证书"],
    },
    {
        "name": "与第三者利害关系说明",
        "aliases": ["第三者利害关系", "利害关系说明", "第三方关系说明"],
    },
    {
        "name": "水资源论证报告书或报告表及审查意见",
        "aliases": ["水资源论证报告", "论证报告表", "审查意见", "论证报告书"],
    },
    {
        "name": "取水工程或者设施建设材料",
        "aliases": ["取水工程", "设施建设", "工程建设", "备案材料"],
    },
]


def _normalize_text(value: Any) -> str:
    return str(value).strip().lower()


def _flatten_materials(application: Dict[str, Any] | List[str] | None, materials: List[str] | None) -> List[str]:
    if materials:
        return [str(item) for item in materials if str(item).strip()]

    if isinstance(application, list):
        return [str(item) for item in application if str(item).strip()]

    if not isinstance(application, dict):
        return []

    collected: List[str] = []
    attachments = application.get("attachments")
    if isinstance(attachments, list):
        collected.extend(str(item) for item in attachments if str(item).strip())

    for field in ["application_form", "id_proof", "subject_qualification", "relation_statement", "assessment_report", "project_materials"]:
        value = application.get(field)
        if value:
            collected.append(str(value))

    for key in ["applicant_name", "applicant_id", "project_name", "water_use", "location"]:
        value = application.get(key)
        if value:
            collected.append(f"{key}:{value}")

    return collected


def _match_required_item(required: Dict[str, Any], submitted_materials: List[str]) -> bool:
    candidates = [required["name"], *required.get("aliases", [])]
    normalized_materials = [_normalize_text(item) for item in submitted_materials]
    return any(
        any(candidate.lower() in material for material in normalized_materials)
        for candidate in candidates
    )


def knowledge_search(query: str, top_k: int = 4) -> List[Dict[str, Any]]:
    if not query.strip():
        return []

    results = vector_store.similarity_search_with_score(query, k=top_k)
    payload: List[Dict[str, Any]] = []
    for rank, (document, score) in enumerate(results, 1):
        metadata = document.metadata or {}
        similarity = 1.0 / (1.0 + max(float(score), 0.0))
        payload.append(
            {
                "rank": rank,
                "content": document.page_content,
                "source": metadata.get("source") or metadata.get("file_path") or "manual",
                "file_path": metadata.get("file_path"),
                "page": metadata.get("page"),
                "chunk": metadata.get("chunk") or metadata.get("chunk_index"),
                "score": float(score),
                "similarity": round(similarity, 6),
                "metadata": metadata,
            }
        )
    return payload


def check_completeness(
    application: Dict[str, Any] | List[str] | None = None,
    materials: List[str] | None = None,
) -> Dict[str, Any]:
    submitted_materials = _flatten_materials(application, materials)

    matched_items = [
        item["name"] for item in CHECKLIST if _match_required_item(item, submitted_materials)
    ]

    missing_required_items = [
        item["name"] for item in CHECKLIST if not _match_required_item(item, submitted_materials)
    ]

    missing_fields = []
    if isinstance(application, dict):
        missing_fields = [field for field in REQUIRED_FIELDS if not application.get(field)]

    issues: List[str] = []
    issues.extend(f"缺少必备材料: {item}" for item in missing_required_items)

    if isinstance(application, dict):
        attachments = application.get("attachments") or []
        if not isinstance(attachments, list):
            issues.append("attachments 必须是文件列表")
        elif not attachments:
            issues.append("未上传任何附件")

    if missing_fields:
        issues.extend(f"缺少字段: {field}" for field in missing_fields)

    complete = len(missing_required_items) == 0 and len(issues) == 0

    return {
        "complete": complete,
        "submitted_materials": submitted_materials,
        "required_checklist": [item["name"] for item in CHECKLIST],
        "matched_items": matched_items,
        "missing_items": missing_required_items,
        "missing_fields": missing_fields,
        "issues": issues,
    }