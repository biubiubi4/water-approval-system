from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from langchain.tools import StructuredTool, Tool
except ImportError:
    pass

from app.mcp_tools import MCP_TOOLS, execute_tool
from app.documents import process_documents
from app.vector_store import vector_store
from app.config import settings
from app.llm_client import llm_client
from app.review_rules import RULE_VERSION, build_completeness_from_rules, evaluate_application_rules
from app.application_form_parser import parse_application_form_fields
from app.compliance_rules import (
    COMPLIANCE_RULE_VERSION,
    build_dimension_queries,
    evaluate_compliance_dimensions,
    has_restrictive_evidence,
    summarize_rag_evidence,
)


SYSTEM_PROMPT = """你是一个专业的涉水审批智能审核助手。请按照以下步骤进行审核：

1. 首先使用 check_completeness 工具检查申请材料的完整性
2. 然后根据申请内容使用 knowledge_search 工具查找相关法规
3. 基于找到的法规和申请材料进行合规性判断

审核重点关注：
- 形式审查：材料是否完整
- 内容规范：信息填写是否正确
- 实质合规：是否符合法规要求

回答格式：
- 审核状态：通过/不通过
- 审核意见：详细说明
- 法规依据：引用相关条款
- 修改建议：如有问题请说明
"""


def create_langchain_tools() -> List[Tool]:
    """创建LangChain工具"""
    tools = []
    
    for mcp_tool in MCP_TOOLS:
        if mcp_tool.name == "knowledge_search":
            def _search_func(query: str, top_k: int = 4) -> str:
                results = execute_tool("knowledge_search", {"query": query, "top_k": top_k})
                return "\n\n".join([
                    f"相关文档{i+1}: {r['content']}" 
                    for i, r in enumerate(results.get("results", []))
                ])
            
            try:
                tools.append(StructuredTool.from_function(
                    func=_search_func,
                    name="knowledge_search",
                    description="从知识库中搜索相关法规和规范文档",
                ))
            except:
                pass
        elif mcp_tool.name == "check_completeness":
            def _check_func(application: Dict) -> str:
                result = execute_tool("check_completeness", {"application": application})
                if result["complete"]:
                    return "材料完整性检查通过"
                else:
                    return f"材料完整性检查不通过:\n- " + "\n- ".join(result["issues"])
            
            try:
                tools.append(StructuredTool.from_function(
                    func=_check_func,
                    name="check_completeness",
                    description="检查申请材料的完整性",
                ))
            except:
                pass
    
    return tools


class WaterApprovalAgent:
    """涉水审批智能审核Agent"""
    
    def __init__(self):
        self.tools = create_langchain_tools()
        self.agent_executor = None
        # optional external LLM client (may be disabled)
        self.llm = llm_client
    
    def review(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行审核"""
        review_mode = str(getattr(settings, "review_mode", "smart") or "smart").lower()
        if review_mode not in {"fast", "smart", "strict"}:
            review_mode = "smart"

        result = {
            "status": "PENDING",
            "message": "",
            "details": {
                "ai_review_trace": {
                    "review_mode": review_mode,
                    "external_ai_enabled": bool(self.llm and getattr(self.llm, "enabled", False)),
                    "provider": getattr(self.llm, "provider", None),
                    "model": getattr(self.llm, "model", None),
                    "used_external_ai": False,
                    "fallback_to_local_rules": False,
                    "fallback_reason": "",
                    "qwen_decision_reason": "",
                    "rule_version": RULE_VERSION,
                    "compliance_rule_version": COMPLIANCE_RULE_VERSION,
                }
            },
            "suggestions": [],
            "knowledge_hits": [],
        }

        ai_review_trace = result["details"]["ai_review_trace"]

        pre_rules = evaluate_application_rules(application_data)
        result["details"]["fast_rules"] = pre_rules
        result["details"]["completeness"] = build_completeness_from_rules(pre_rules)
        if pre_rules.get("should_block"):
            ai_review_trace["fallback_to_local_rules"] = True
            ai_review_trace["fallback_reason"] = "fast_rule_blocker_before_document_parse"
            print("[规则审查] 命中硬性规则，跳过附件解析与 Qwen 审查")
            return self._reject_by_fast_rules(result, pre_rules)

        file_paths = self._resolve_application_file_paths(application_data)
        loaded_documents = []
        if file_paths:
            loaded_documents = process_documents(file_paths)
            result["details"]["attachment_documents"] = [
                {
                    "file_path": doc.metadata.get("file_path"),
                    "source": doc.metadata.get("source"),
                    "reader": doc.metadata.get("reader"),
                    "page": doc.metadata.get("page"),
                    "chunk_index": doc.metadata.get("chunk_index"),
                    "document_cache_hit": doc.metadata.get("document_cache_hit"),
                    "document_cache_key": doc.metadata.get("document_cache_key"),
                    "preview": doc.page_content[:300],
                }
                for doc in loaded_documents
            ]
            result["details"]["document_cache"] = self._build_document_cache_summary(loaded_documents)

            if not loaded_documents:
                result["status"] = "ERROR"
                result["message"] = "审批时无法加载本地附件"
                result["details"]["attachment_paths"] = [str(path) for path in file_paths]
                return result
        else:
            result["details"]["attachment_documents"] = []
            result["details"]["document_cache"] = {
                "enabled": bool(getattr(settings, "document_cache_enabled", True)),
                "total_chunks": 0,
                "hit_chunks": 0,
                "miss_chunks": 0,
                "files": [],
            }

        field_validity_checker = self._field_validity_checker if review_mode in {"smart", "strict"} else None
        full_rules = evaluate_application_rules(
            application_data,
            loaded_documents,
            field_validity_checker=field_validity_checker,
        )
        result["details"]["fast_rules"] = full_rules
        result["details"]["completeness"] = build_completeness_from_rules(full_rules)
        if full_rules.get("should_block"):
            ai_review_trace["fallback_to_local_rules"] = True
            ai_review_trace["fallback_reason"] = "fast_rule_blocker_after_document_parse"
            print("[规则审查] 附件解析后命中硬性规则，跳过 Qwen 审查")
            return self._reject_by_fast_rules(result, full_rules)
        
        # 步骤2：搜索相关法规
        try:
            search_query = self._build_search_query(application_data, loaded_documents)
            search_result = execute_tool("knowledge_search", {"query": search_query, "top_k": 3})
            result["knowledge_hits"] = search_result.get("results", [])
        except Exception as e:
            print(f"知识库搜索失败: {e}")

        application_form_fields = parse_application_form_fields(loaded_documents)
        result["details"]["application_form_fields"] = application_form_fields
        rag_evidence = self._search_rag_evidence_by_dimension(application_data, application_form_fields)
        result["details"]["rag_evidence"] = summarize_rag_evidence(rag_evidence)

        local_compliance_result = self._check_compliance(
            application_data,
            result["knowledge_hits"],
            application_form_fields,
            rag_evidence,
        )
        result["details"]["compliance"] = local_compliance_result
        if local_compliance_result.get("violations"):
            ai_review_trace["fallback_to_local_rules"] = True
            ai_review_trace["fallback_reason"] = "local_compliance_blocker"
            print("[合规审查] 命中本地合规硬性问题，跳过 Qwen 审查")
            self._apply_local_decision(result, local_compliance_result)
            return result

        # 步骤3：合规性判断（优先使用外部AI，如未配置则回退到本地规则）
        should_call_qwen, decision_reason = self._should_call_external_ai(
            review_mode,
            full_rules,
            result["knowledge_hits"],
            loaded_documents,
            local_compliance_result,
            rag_evidence,
        )
        ai_review_trace["qwen_decision_reason"] = decision_reason

        if should_call_qwen and self.llm and getattr(self.llm, "enabled", False):
            llm_resp = self.llm.generate_review(
                application_data,
                result["knowledge_hits"],
                loaded_documents,
                local_compliance_result,
                result["details"]["rag_evidence"],
            )
            if llm_resp is None:
                # 没有有效配置，回退到本地实现
                ai_review_trace["fallback_to_local_rules"] = True
                ai_review_trace["fallback_reason"] = "external_ai_disabled_or_not_configured"
                print("[AI审核] 未调用外部AI，使用本地规则审查")
                compliance_result = local_compliance_result
                result["details"]["compliance"] = compliance_result
                self._apply_local_decision(result, compliance_result)
            elif isinstance(llm_resp, dict) and llm_resp.get("error"):
                # 外部AI调用失败 — 记录错误并回退
                ai_review_trace["fallback_to_local_rules"] = True
                ai_review_trace["fallback_reason"] = str(llm_resp.get("error", "external_ai_error"))
                print(f"[AI审核] 外部AI审查失败，使用本地规则审查: {ai_review_trace['fallback_reason']}")
                result["details"]["llm_error"] = llm_resp
                compliance_result = local_compliance_result
                result["details"]["compliance"] = compliance_result
                self._apply_local_decision(result, compliance_result)
            else:
                # 使用外部AI返回的结果（期望与现有结果结构兼容）
                # 合并外部结果到返回值，同时保留本地完整性检查、附件解析和检索信息。
                ai_review_trace["used_external_ai"] = True
                external_status_present = "status" in llm_resp
                external_details = llm_resp.get("details") if isinstance(llm_resp.get("details"), dict) else {}
                for key, value in llm_resp.items():
                    if key != "details":
                        result[key] = value
                result["details"]["external_ai"] = external_details
                if isinstance(external_details.get("compliance"), dict):
                    result["details"]["external_ai"]["compliance"] = external_details["compliance"]
                result.setdefault("knowledge_hits", result.get("knowledge_hits", []))
                print(f"[AI审核] 使用外部AI审查结果: status={result.get('status')}")
                # 如果外部结果没有 status 等字段，不改变本地默认逻辑
                if not external_status_present:
                    ai_review_trace["fallback_to_local_rules"] = True
                    ai_review_trace["fallback_reason"] = "external_ai_response_missing_status"
                    print("[AI审核] 外部AI结果缺少 status，使用本地规则审查")
                    compliance_result = local_compliance_result
                    result["details"]["compliance"] = compliance_result
                    self._apply_local_decision(result, compliance_result)
        else:
            ai_review_trace["fallback_to_local_rules"] = True
            ai_review_trace["fallback_reason"] = decision_reason
            print(f"[AI审核] 未调用外部AI，使用本地规则审查: {decision_reason}")
            compliance_result = local_compliance_result
            result["details"]["compliance"] = compliance_result

        # 检查外部LLM是否已经设置了status，如果已设置则尊重其判断，不覆盖
        llm_status_set = "status" in result and result["status"] not in ("PENDING", "ERROR")
        
        if not llm_status_set:
            completeness_failed = not bool(result["details"].get("completeness", {}).get("complete", True))
            compliance = result["details"].get("compliance", {})
            compliance_failed = bool(compliance.get("violations")) or compliance.get("status") == "FAIL"

            if completeness_failed or compliance_failed:
                result["status"] = "REJECTED"
                if completeness_failed and compliance_failed:
                    result["message"] = "申请材料不完整且存在合规性问题"
                elif completeness_failed:
                    result["message"] = "申请材料不完整"
                else:
                    result["message"] = "申请不符合法规要求"

                suggestions: List[str] = []
                completeness_issues = result["details"].get("completeness", {}).get("issues") or []
                compliance_violations = result["details"].get("compliance", {}).get("violations") or []
                suggestions.extend(str(item) for item in completeness_issues)
                suggestions.extend(str(item) for item in compliance_violations)
                result["suggestions"] = suggestions
            else:
                result["status"] = "APPROVED"
                result["message"] = "申请审核通过"
        
        return result

    def _reject_by_fast_rules(self, result: Dict[str, Any], rule_result: Dict[str, Any]) -> Dict[str, Any]:
        suggestions = [str(issue.get("message")) for issue in rule_result.get("blockers", [])]
        if not suggestions:
            suggestions = [str(issue.get("message")) for issue in rule_result.get("issues", [])]

        result["status"] = "REJECTED"
        result["message"] = "申请材料存在硬性规则问题"
        result["suggestions"] = suggestions
        result["details"]["compliance"] = {
            "pass": False,
            "status": "FAIL",
            "dimensions": [],
            "violations": suggestions,
            "warnings": [],
        }
        return result

    def _should_call_external_ai(
        self,
        review_mode: str,
        rule_result: Dict[str, Any],
        knowledge_hits: List[Dict[str, Any]],
        documents: List[Any],
        compliance_result: Dict[str, Any] | None = None,
        rag_evidence: Dict[str, Any] | None = None,
    ) -> tuple[bool, str]:
        if review_mode == "fast":
            return False, "review_mode_fast"

        if not (self.llm and getattr(self.llm, "enabled", False)):
            return False, "external_ai_disabled"

        if review_mode == "strict":
            return True, "review_mode_strict"

        if rule_result.get("should_use_external_ai"):
            return True, "fast_rule_warning_requires_review"

        warning_count = len((compliance_result or {}).get("warnings") or [])
        if warning_count >= 2:
            return True, "multiple_compliance_warnings"

        if self._has_restrictive_knowledge(knowledge_hits):
            return True, "restrictive_knowledge_hit"

        if has_restrictive_evidence(rag_evidence):
            return True, "restrictive_rag_evidence_hit"

        if self._has_complex_documents(documents):
            return True, "complex_attachment_documents"

        return False, "smart_mode_no_risk_signal"

    def _has_restrictive_knowledge(self, knowledge_hits: List[Dict[str, Any]]) -> bool:
        keywords = ["禁止", "不得", "限制", "不予批准", "保护区"]
        for hit in knowledge_hits:
            content = str(hit.get("content") or "")
            if any(keyword in content for keyword in keywords):
                return True
        return False

    def _has_complex_documents(self, documents: List[Any]) -> bool:
        if len(documents) >= 4:
            return True
        total_chars = sum(len(str(getattr(document, "page_content", "") or "")) for document in documents)
        return total_chars >= 1200

    def _build_document_cache_summary(self, documents: List[Any]) -> Dict[str, Any]:
        files: Dict[str, Dict[str, Any]] = {}
        hit_chunks = 0
        miss_chunks = 0

        for document in documents:
            metadata = getattr(document, "metadata", {}) or {}
            file_path = str(metadata.get("file_path") or metadata.get("source") or "附件")
            cache_hit = metadata.get("document_cache_hit")
            if cache_hit is True:
                hit_chunks += 1
            elif cache_hit is False:
                miss_chunks += 1

            item = files.setdefault(
                file_path,
                {
                    "file_path": file_path,
                    "source": metadata.get("source"),
                    "reader": metadata.get("reader"),
                    "document_cache_hit": cache_hit,
                    "chunk_count": 0,
                },
            )
            item["chunk_count"] += 1
            if item.get("reader") is None and metadata.get("reader"):
                item["reader"] = metadata.get("reader")

        return {
            "enabled": bool(getattr(settings, "document_cache_enabled", True)),
            "total_chunks": len(documents),
            "hit_chunks": hit_chunks,
            "miss_chunks": miss_chunks,
            "files": list(files.values()),
        }
    
    def _build_search_query(self, application: Dict[str, Any], documents: List[Any] | None = None) -> str:
        """构建搜索查询"""
        parts = []
        if application.get("water_use"):
            parts.append(f"取水用途：{application['water_use']}")
        if application.get("location"):
            parts.append(f"取水地点：{application['location']}")
        if application.get("project_name"):
            parts.append(f"项目：{application['project_name']}")

        if documents:
            snippets = []
            for document in documents[:3]:
                text = (getattr(document, "page_content", "") or "").strip()
                if text:
                    snippets.append(text[:200])
            if snippets:
                parts.append("附件摘要：" + " ".join(snippets))
        
        return " ".join(parts) if parts else "取水许可审批 水法"

    def _search_rag_evidence_by_dimension(
        self,
        application: Dict[str, Any],
        application_form_fields: Dict[str, Any],
    ) -> Dict[str, Any]:
        evidence: Dict[str, Any] = {}
        for dimension, query in build_dimension_queries(application, application_form_fields).items():
            try:
                search_result = execute_tool("knowledge_search", {"query": query, "top_k": 2})
                evidence[dimension] = {
                    "query": query,
                    "hits": search_result.get("results", []),
                }
            except Exception as error:
                print(f"维度法规检索失败: dimension={dimension}, error={error}")
                evidence[dimension] = {
                    "query": query,
                    "hits": [],
                    "error": str(error),
                }
        return evidence

    def _resolve_application_file_paths(self, application: Dict[str, Any]) -> List[Path]:
        raw_paths = application.get("file_paths") or application.get("file_names") or application.get("attachments") or []
        if not isinstance(raw_paths, list):
            return []

        upload_dir = Path(__file__).resolve().parent.parent.parent / "java-backend" / "uploads"
        resolved_paths: List[Path] = []
        for item in raw_paths:
            value = str(item).strip()
            if not value:
                continue

            candidate = Path(value)
            if candidate.is_absolute():
                resolved_paths.append(candidate)
                continue

            direct_candidate = upload_dir / value
            if direct_candidate.exists():
                resolved_paths.append(direct_candidate)
                continue

            resolved_paths.append(upload_dir / candidate.name)

        return resolved_paths
    
    def _check_compliance(
        self,
        application: Dict[str, Any],
        knowledge_hits: List[Dict],
        application_form_fields: Dict[str, Any] | None = None,
        rag_evidence: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """合规性检查"""
        return evaluate_compliance_dimensions(
            application,
            knowledge_hits,
            application_form_fields,
            rag_evidence,
        )

    def _field_validity_checker(self, fields: List[Dict[str, Any]], instruction: str) -> Dict[str, Any] | None:
        if not (self.llm and getattr(self.llm, "enabled", False)):
            return None
        return self.llm.validate_field_values(fields, instruction)

    def _apply_local_decision(self, result: Dict[str, Any], compliance_result: Dict[str, Any]) -> None:
        if compliance_result.get("violations"):
            result["status"] = "REJECTED"
            result["message"] = "申请不符合法规要求"
            result["suggestions"] = compliance_result["violations"]
        else:
            result["status"] = "APPROVED"
            result["message"] = "申请审核通过"


agent: Optional[WaterApprovalAgent] = None


def get_agent() -> WaterApprovalAgent:
    """获取Agent单例"""
    global agent
    if agent is None:
        agent = WaterApprovalAgent()
    return agent
