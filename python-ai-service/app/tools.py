from __future__ import annotations

import re
from typing import Any, Dict, List

from app.config import settings
from app.vector_store import vector_store


REQUIRED_FIELDS = ["applicant_name", "applicant_id", "project_name", "attachments"]


CHECKLIST = [
    {
        "name": "取水许可申请书",
        "aliases": ["申请书", "取水申请书", "申请表", "water application form"],
    },
    {
        "name": "营业执照",
        "aliases": ["营业执照", "主体资格", "法人证书", "信用代码证"],
    },
    {
        "name": "身份证",
        "aliases": ["身份证", "身份证明", "法人证明", "法人身份证", "id card"],
    },
]

_STOPWORDS = {
    "以及",
    "和",
    "与",
    "或",
    "的",
    "请",
    "是否",
    "如何",
    "什么",
    "哪些",
    "相关",
    "进行",
    "需要",
    "关于",
    "材料",
    "文件",
    "内容",
    "问题",
    "办理",
    "审批",
    "查询",
    "检索",
    "审核",
    "法律",
    "法规",
}
 

def _normalize_text(value: Any) -> str:
    return str(value).strip().lower()


def _normalize_query(query: str) -> str:
    text = _normalize_text(query)
    text = re.sub(r"[\s\t\r\n]+", " ", text)
    text = re.sub(r"[，。；；、,.!?！？：:()（）\[\]{}<>]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _extract_query_terms(query: str) -> List[str]:
    raw_chunks = re.findall(r"[\u4e00-\u9fffA-Za-z0-9]+", _normalize_query(query))
    terms: List[str] = []

    for chunk in raw_chunks:
        if not chunk:
            continue
        if chunk in _STOPWORDS:
            continue
        if chunk not in terms:
            terms.append(chunk)

        if re.fullmatch(r"[\u4e00-\u9fff]+", chunk) and len(chunk) >= 4:
            for size in (2, 3):
                for index in range(len(chunk) - size + 1):
                    gram = chunk[index:index + size]
                    if gram not in _STOPWORDS and gram not in terms:
                        terms.append(gram)

    return terms[:16]


def _build_query_variants(query: str) -> List[str]:
    normalized = _normalize_query(query)
    terms = _extract_query_terms(query)

    variants = [query.strip()]
    if normalized and normalized not in variants:
        variants.append(normalized)

    if terms:
        keyword_query = " ".join(terms[: min(len(terms), 8)])
        if keyword_query not in variants:
            variants.append(keyword_query)

    clauses = [part.strip() for part in re.split(r"[，。；、,.!?！？：:]+", query) if part.strip()]
    for clause in clauses[: max(0, int(settings.semantic_search_max_variants) - len(variants))]:
        if clause not in variants:
            variants.append(clause)

    max_variants = max(1, int(settings.semantic_search_max_variants))
    return variants[:max_variants]


def _candidate_key(document: Any, metadata: Dict[str, Any]) -> str:
    return "|".join([
        str(metadata.get("source") or ""),
        str(metadata.get("file_path") or ""),
        str(metadata.get("page") or ""),
        str(metadata.get("chunk") or metadata.get("chunk_index") or ""),
        document.page_content[:300],
    ])


def _lexical_overlap_score(query_terms: List[str], content: str, metadata: Dict[str, Any]) -> float:
    if not query_terms:
        return 0.0

    haystack = _normalize_query(
        " ".join([
            content,
            str(metadata.get("source") or ""),
            str(metadata.get("file_path") or ""),
        ])
    )

    matched_weight = 0.0
    total_weight = 0.0
    for term in query_terms:
        weight = max(1.0, float(len(term)))
        total_weight += weight
        if term and term in haystack:
            matched_weight += weight

    if total_weight <= 0:
        return 0.0

    return min(1.0, matched_weight / total_weight)


def _combine_scores(vector_similarity: float, lexical_score: float) -> float:
    return (
        vector_similarity * float(settings.semantic_search_vector_weight)
        + lexical_score * float(settings.semantic_search_lexical_weight)
    )


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

    try:
        candidate_k = max(int(top_k) * 4, int(settings.semantic_search_candidate_k))
        variants = _build_query_variants(query)
        query_terms = _extract_query_terms(query)

        candidates: Dict[str, Dict[str, Any]] = {}
        for variant_index, variant in enumerate(variants, start=1):
            results = vector_store.similarity_search_with_score(variant, k=candidate_k)
            for document, score in results:
                metadata = document.metadata or {}
                key = _candidate_key(document, metadata)
                vector_similarity = 1.0 / (1.0 + max(float(score), 0.0))
                lexical_score = _lexical_overlap_score(query_terms, document.page_content, metadata)
                combined_score = _combine_scores(vector_similarity, lexical_score)

                existing = candidates.get(key)
                if existing is None or combined_score > existing["rerank_score"]:
                    candidates[key] = {
                        "document": document,
                        "metadata": metadata,
                        "raw_score": float(score),
                        "vector_similarity": round(vector_similarity, 6),
                        "lexical_score": round(lexical_score, 6),
                        "rerank_score": round(combined_score, 6),
                        "matched_terms": [term for term in query_terms if term in _normalize_query(document.page_content)],
                        "query_variant": variant,
                        "query_variant_index": variant_index,
                    }
    except Exception as error:
        message = str(error)
        if (
            "Error loading hnsw index" in message
            or "Error constructing hnsw segment reader" in message
            or "Error sending backfill request to compactor" in message
        ):
            print(f"知识库索引损坏，返回空检索结果: {error}")
            return []
        raise

    ranked_candidates = sorted(
        candidates.values(),
        key=lambda item: (
            item["rerank_score"],
            item["vector_similarity"],
            -item["raw_score"],
        ),
        reverse=True,
    )

    payload: List[Dict[str, Any]] = []
    for rank, item in enumerate(ranked_candidates[:top_k], 1):
        document = item["document"]
        metadata = item["metadata"]
        payload.append(
            {
                "rank": rank,
                "content": document.page_content,
                "source": metadata.get("source") or metadata.get("file_path") or "manual",
                "file_path": metadata.get("file_path"),
                "page": metadata.get("page"),
                "chunk": metadata.get("chunk") or metadata.get("chunk_index"),
                "score": item["rerank_score"],
                "similarity": item["rerank_score"],
                "vector_similarity": item["vector_similarity"],
                "lexical_score": item["lexical_score"],
                "raw_score": item["raw_score"],
                "matched_terms": item["matched_terms"],
                "query_variant": item["query_variant"],
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