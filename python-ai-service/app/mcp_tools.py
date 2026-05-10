from __future__ import annotations

from typing import Any, Dict, List
from pydantic import BaseModel, Field

from app.tools import knowledge_search, check_completeness


class MCPTool(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]


class KnowledgeSearchArgs(BaseModel):
    query: str = Field(..., description="要搜索的问题或关键词")
    top_k: int = Field(default=4, description="返回的相关文档数量")


class CheckCompletenessArgs(BaseModel):
    application: Dict[str, Any] = Field(..., description="申请材料数据")


# MCP工具定义
MCP_TOOLS: List[MCPTool] = [
    MCPTool(
        name="knowledge_search",
        description="从知识库中搜索相关法规和规范文档，用于合规性检查",
        input_schema=KnowledgeSearchArgs.model_json_schema()
    ),
    MCPTool(
        name="check_completeness",
        description="检查申请材料的完整性，验证必填字段和附件",
        input_schema=CheckCompletenessArgs.model_json_schema()
    )
]


def execute_tool(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """执行MCP工具"""
    if tool_name == "knowledge_search":
        return {
            "results": knowledge_search(
                query=args.get("query", ""),
                top_k=args.get("top_k", 4)
            )
        }
    elif tool_name == "check_completeness":
        return check_completeness(
            application=args.get("application", {})
        )
    else:
        raise ValueError(f"未知工具: {tool_name}")
