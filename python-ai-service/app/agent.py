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
        result = {
            "status": "PENDING",
            "message": "",
            "details": {},
            "suggestions": [],
            "knowledge_hits": [],
        }

        file_paths = self._resolve_application_file_paths(application_data)
        loaded_documents = []
        if file_paths:
            loaded_documents = process_documents(file_paths)
            result["details"]["attachment_documents"] = [
                {
                    "file_path": doc.metadata.get("file_path"),
                    "source": doc.metadata.get("source"),
                    "chunk_index": doc.metadata.get("chunk_index"),
                    "preview": doc.page_content[:300],
                }
                for doc in loaded_documents
            ]

            if not loaded_documents:
                result["status"] = "ERROR"
                result["message"] = "审批时无法加载本地附件"
                result["details"]["attachment_paths"] = [str(path) for path in file_paths]
                return result
        else:
            result["details"]["attachment_documents"] = []
        
        # 步骤1：完整性检查
        try:
            completeness = execute_tool("check_completeness", {"application": application_data})
            completeness["status"] = "PASS" if completeness.get("complete") else "FAIL"
            result["details"]["completeness"] = completeness
        except Exception as e:
            result["status"] = "ERROR"
            result["message"] = f"完整性检查失败: {str(e)}"
            return result
        
        # 步骤2：搜索相关法规
        try:
            search_query = self._build_search_query(application_data, loaded_documents)
            search_result = execute_tool("knowledge_search", {"query": search_query, "top_k": 3})
            result["knowledge_hits"] = search_result.get("results", [])
        except Exception as e:
            print(f"知识库搜索失败: {e}")

        # 步骤3：合规性判断（优先使用外部AI，如未配置则回退到本地规则）
        if self.llm and getattr(self.llm, "enabled", False):
            llm_resp = self.llm.generate_review(application_data, result["knowledge_hits"], loaded_documents)
            if llm_resp is None:
                # 没有有效配置，回退到本地实现
                compliance_result = self._check_compliance(application_data, result["knowledge_hits"])
                result["details"]["compliance"] = compliance_result
                self._apply_local_decision(result, compliance_result)
            elif isinstance(llm_resp, dict) and llm_resp.get("error"):
                # 外部AI调用失败 — 记录错误并回退
                result["details"]["llm_error"] = llm_resp
                compliance_result = self._check_compliance(application_data, result["knowledge_hits"])
                result["details"]["compliance"] = compliance_result
                self._apply_local_decision(result, compliance_result)
            else:
                # 使用外部AI返回的结果（期望与现有结果结构兼容）
                # 合并外部结果到返回值（保留本地知识命中以便排查）
                result.update(llm_resp)
                result.setdefault("knowledge_hits", result.get("knowledge_hits", []))
                # 如果外部结果没有 status 等字段，不改变本地默认逻辑
                if "status" not in result:
                    compliance_result = self._check_compliance(application_data, result["knowledge_hits"])
                    result["details"]["compliance"] = compliance_result
                    self._apply_local_decision(result, compliance_result)
        else:
            compliance_result = self._check_compliance(application_data, result["knowledge_hits"])
            compliance_result["status"] = "PASS" if compliance_result.get("pass") else "FAIL"
            result["details"]["compliance"] = compliance_result

        # 检查外部LLM是否已经设置了status，如果已设置则尊重其判断，不覆盖
        llm_status_set = "status" in result and result["status"] not in ("PENDING", "ERROR")
        
        if not llm_status_set:
            completeness_failed = not bool(result["details"].get("completeness", {}).get("complete", True))
            compliance_failed = not bool(result["details"].get("compliance", {}).get("pass", True))

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
    
    def _check_compliance(self, application: Dict[str, Any], knowledge_hits: List[Dict]) -> Dict[str, Any]:
        """合规性检查"""
        violations = []
        
        required_fields = ["project_name", "applicant_name", "applicant_id"]
        missing_content = [f for f in required_fields if not application.get(f)]
        if missing_content:
            violations.append(f"缺少必填内容：{', '.join(missing_content)}")
        
        water_use = application.get("water_use") or ""
        if "饮用水" in water_use:
            violations.append("饮用水源保护区禁止新设取水口")
        
        for hit in knowledge_hits:
            if "禁止" in hit.get("content", ""):
                content = hit.get("content", "")
                violations.append(f"相关法规限制：{content[:50]}...")
        
        return {
            "violations": violations,
            "pass": len(violations) == 0,
        }

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
