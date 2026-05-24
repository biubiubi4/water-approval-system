from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.config import settings
from app.service import (
    add_knowledge_files,
    add_knowledge_text,
    create_knowledge_record,
    delete_knowledge_record,
    get_knowledge_record,
    list_knowledge_records,
    update_knowledge_record,
)
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


class CompletenessRequest(BaseModel):
    application: Dict[str, Any] = Field(default_factory=dict, description="申请数据")
    materials: List[str] = Field(default_factory=list, description="申请材料名称列表")


class KnowledgeRecordIn(BaseModel):
    content: str = Field(..., description="知识内容")
    source: str = Field(default="manual", description="知识来源")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="附加元数据")


class KnowledgeRecordUpdateIn(BaseModel):
    content: str = Field(..., description="知识内容")
    source: str = Field(default="manual", description="知识来源")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="附加元数据")


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


@app.get("/api/knowledge/stats")
def api_knowledge_stats() -> Dict[str, Any]:
    return list_knowledge_records()["summary"]


@app.get("/api/knowledge/records")
def api_list_knowledge_records(
    q: str | None = None,
    source: str | None = None,
    record_type: str | None = None,
) -> Dict[str, Any]:
    return list_knowledge_records(query=q, source=source, record_type=record_type)


@app.get("/api/knowledge/records/{record_id}")
def api_get_knowledge_record(record_id: str) -> Dict[str, Any]:
    try:
        return get_knowledge_record(record_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post("/api/knowledge/records")
def api_create_knowledge_record(payload: KnowledgeRecordIn) -> Dict[str, Any]:
    return create_knowledge_record(payload.content, source=payload.source, metadata=payload.metadata)


@app.put("/api/knowledge/records/{record_id}")
def api_update_knowledge_record(record_id: str, payload: KnowledgeRecordUpdateIn) -> Dict[str, Any]:
    try:
        return update_knowledge_record(
            record_id,
            payload.content,
            source=payload.source,
            metadata=payload.metadata,
        )
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.delete("/api/knowledge/records/{record_id}")
def api_delete_knowledge_record(record_id: str) -> Dict[str, Any]:
    try:
        return delete_knowledge_record(record_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post("/api/knowledge/delete")
def api_delete_knowledge(payload: Dict[str, list]) -> Dict[str, Any]:
    names = payload.get("files") or []
    # 删除存储的文件（uploads 目录）
    saved_dir = settings.chroma_dir.parent / "uploads"
    for name in names:
        try:
            p = saved_dir / name
            if p.exists():
                p.unlink()
        except Exception as e:
            print(f"删除上传文件失败 {name}: {e}")

    from app.service import remove_knowledge_files
    return remove_knowledge_files(names)


@app.post("/api/review")
def api_review(payload: ReviewRequest) -> Dict[str, Any]:
    agent = get_agent()
    result = agent.review(payload.application)
    return result


@app.post("/api/check-completeness")
def api_check_completeness(payload: CompletenessRequest) -> Dict[str, Any]:
    return execute_tool(
        "check_completeness",
        {"application": payload.application, "materials": payload.materials},
    )


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
