# Python AI Service

这是涉水审批智能审核系统的 Python AI 服务骨架，提供以下能力：

- 文档解析：支持 PDF、Word、文本文件
- 知识库：基于 ChromaDB 的本地向量库
- LangChain：使用 LangChain 的 `Embeddings` 与 `Chroma` 组件
- 核心工具：`knowledge_search`、`check_completeness`
- MCP 暴露：`GET /api/mcp/tools` 与 `POST /api/mcp/{tool_name}`

## 启动

```bash
cd python-ai-service
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

如果需要独立的 MCP 启动入口，可以运行：

```bash
python -m app.mcp_server
```

## 接口

- `GET /health`：健康检查
- `POST /api/knowledge/add`：添加知识文本
- `POST /api/knowledge/upload`：上传 PDF / Word / TXT 文件并入库
- `GET /api/knowledge/search?q=...`：知识检索
- `POST /api/check-completeness`：完整性检查（支持 `application` 或 `materials`）
- `POST /api/review`：合规性初审