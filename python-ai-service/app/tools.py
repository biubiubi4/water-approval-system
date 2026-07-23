from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any, Dict, List

from app.config import settings
from app.review_rules import (
    build_completeness_from_rules,
    collect_material_names,
    evaluate_application_rules,
)
from app.vector_store import vector_store

try:
    from langchain_core.documents import Document
except ImportError:
    from langchain.schema import Document


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


def _combine_scores(vector_similarity: float, lexical_score: float, bm25_score: float) -> float:
    return (
        vector_similarity * float(settings.semantic_search_vector_weight)
        + lexical_score * float(settings.semantic_search_lexical_weight)
        + bm25_score * float(settings.semantic_search_bm25_weight)
    )


def _bm25_candidates(query_terms: List[str]) -> List[Dict[str, Any]]:
    """Perform sparse lexical recall over the local Chroma corpus.

    Chroma's vector search can miss an exact regulation title, article number,
    or place name. This lightweight BM25 pass complements it without adding a
    separate search service.
    """
    if not query_terms:
        return []

    raw = vector_store._collection.get(include=["documents", "metadatas"])
    documents = raw.get("documents") or []
    metadatas = raw.get("metadatas") or []
    corpus_terms = [_extract_query_terms(str(content or "")) for content in documents]
    corpus_size = len(corpus_terms)
    if corpus_size == 0:
        return []

    document_frequency = Counter(
        term
        for terms in corpus_terms
        for term in set(terms)
    )
    average_length = sum(len(terms) for terms in corpus_terms) / corpus_size or 1.0
    k1, b = 1.5, 0.75
    scored: List[Dict[str, Any]] = []
    for index, terms in enumerate(corpus_terms):
        term_frequency = Counter(terms)
        length = max(len(terms), 1)
        score = 0.0
        for term in query_terms:
            frequency = term_frequency.get(term, 0)
            if not frequency:
                continue
            idf = math.log(1.0 + (corpus_size - document_frequency[term] + 0.5) / (document_frequency[term] + 0.5))
            score += idf * (frequency * (k1 + 1.0)) / (frequency + k1 * (1.0 - b + b * length / average_length))
        if score > 0:
            scored.append({
                "document": Document(page_content=str(documents[index] or ""), metadata=metadatas[index] if index < len(metadatas) else {}),
                "bm25_raw_score": score,
            })

    scored.sort(key=lambda item: item["bm25_raw_score"], reverse=True)
    if not scored:
        return []
    max_score = scored[0]["bm25_raw_score"]
    for item in scored:
        item["bm25_score"] = round(item["bm25_raw_score"] / max_score, 6) if max_score else 0.0
    return scored[: max(1, int(settings.semantic_search_bm25_candidate_k))]


def _flatten_materials(application: Dict[str, Any] | List[str] | None, materials: List[str] | None) -> List[str]:
    return collect_material_names(application, materials)


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
                combined_score = _combine_scores(vector_similarity, lexical_score, 0.0)

                existing = candidates.get(key)
                if existing is None or combined_score > existing["rerank_score"]:
                    candidates[key] = {
                        "document": document,
                        "metadata": metadata,
                        "raw_score": float(score),
                        "vector_similarity": round(vector_similarity, 6),
                        "lexical_score": round(lexical_score, 6),
                        "bm25_score": 0.0,
                        "rerank_score": round(combined_score, 6),
                        "matched_terms": [term for term in query_terms if term in _normalize_query(document.page_content)],
                        "query_variant": variant,
                        "query_variant_index": variant_index,
                    }

        for item in _bm25_candidates(query_terms):
            document = item["document"]
            metadata = document.metadata or {}
            key = _candidate_key(document, metadata)
            lexical_score = _lexical_overlap_score(query_terms, document.page_content, metadata)
            bm25_score = float(item["bm25_score"])
            combined_score = _combine_scores(0.0, lexical_score, bm25_score)
            existing = candidates.get(key)
            if existing is None:
                candidates[key] = {
                    "document": document,
                    "metadata": metadata,
                    "raw_score": 0.0,
                    "vector_similarity": 0.0,
                    "lexical_score": round(lexical_score, 6),
                    "bm25_score": round(bm25_score, 6),
                    "rerank_score": round(combined_score, 6),
                    "matched_terms": [term for term in query_terms if term in _normalize_query(document.page_content)],
                    "query_variant": "bm25",
                    "query_variant_index": 0,
                }
            else:
                existing["bm25_score"] = max(existing["bm25_score"], round(bm25_score, 6))
                existing["rerank_score"] = round(_combine_scores(existing["vector_similarity"], existing["lexical_score"], existing["bm25_score"]), 6)
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
                "bm25_score": item["bm25_score"],
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
    rule_result = evaluate_application_rules(
        application if isinstance(application, dict) else {},
        materials=submitted_materials,
        check_fields=isinstance(application, dict),
    )
    return build_completeness_from_rules(rule_result, submitted_materials=submitted_materials)
