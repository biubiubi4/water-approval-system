from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel, Field

from app.config import settings
from app.service import add_knowledge_files, add_knowledge_text
from app.agent import get_agent
from app.mcp_tools import MCP_TOOLS, execute_tool
from app.vector_store import init_vector_store, vector_store

app = FastAPI(title=settings.app_name, version="0.1.0")


class KnowledgeTextIn(BaseModel):
    text: str = Field(..., description="要加入知识库的文本")
    source: str = Field(default="manual", description="知识来源")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="附加元数据")


class ReviewRequest(BaseModel):
    application: Dict[str, Any] = Field(default_factory=dict, description="申请数据")


@app.get("/")
def root() -> Dict[str, str]:
    return {
        "message": "涉水审批智能审核AI服务运行中",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "water-approval-ai"}


@app.get("/api/mcp/tools")
def get_mcp_tools() -> Dict[str, Any]:
    return {
        "tools": [tool.model_dump() for tool in MCP_TOOLS]
    }


@app.post("/api/mcp/{tool_name}")
def call_mcp_tool(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    try:
        result = execute_tool(tool_name, args)
        return {
            "success": True,
            "tool": tool_name,
            "result": result
        }
    except Exception as e:
        return {
            "success": False,
            "tool": tool_name,
            "error": str(e)
        }


@app.post("/api/knowledge/add")
def api_add_knowledge(payload: KnowledgeTextIn) -> Dict[str, Any]:
    return add_knowledge_text(payload.text, source=payload.source, metadata=payload.metadata)


@app.post("/api/knowledge/upload")
async def api_upload_knowledge(files: List[UploadFile] | None = File(default=None)) -> Dict[str, Any]:
    saved_dir = settings.chroma_dir.parent / "uploads"
    saved_dir.mkdir(parents=True, exist_ok=True)

    saved_paths: List[Path] = []
    for upload in files or []:
        destination = saved_dir / upload.filename
        content = await upload.read()
        destination.write_bytes(content)
        saved_paths.append(destination)

    return add_knowledge_files(saved_paths)


@app.get("/api/knowledge/search")
def api_search_knowledge(q: str, top_k: int = 4) -> Dict[str, Any]:
    from app.tools import knowledge_search
    return {"query": q, "results": knowledge_search(q, top_k=top_k)}


@app.post("/api/review")
def api_review(payload: ReviewRequest) -> Dict[str, Any]:
    agent = get_agent()
    result = agent.review(payload.application)
    return result


@app.post("/api/check-completeness")
def api_check_completeness(payload: ReviewRequest) -> Dict[str, Any]:
    return execute_tool("check_completeness", {"application": payload.application})


if __name__ == "__main__":
    import uvicorn
    print("启动涉水审批智能审核AI服务...")
    print(f"配置目录: {settings.chroma_dir}")
    
    print("初始化向量数据库...")
    init_vector_store()
    
    print("加载示例法规文档...")
    from app.knowledge_base import init_sample_knowledge
    init_sample_knowledge()
    
    print("服务启动完成！")
    print(f"访问地址: http://127.0.0.1:{settings.port}")
    print(f"API文档: http://127.0.0.1:{settings.port}/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
