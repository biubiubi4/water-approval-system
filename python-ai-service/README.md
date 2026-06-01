# Python AI Service

这是涉水审批智能审核系统的 Python AI 服务，负责知识检索、材料完整性检查、合规性初审和 MCP 工具暴露。

## 技术栈

- FastAPI
- LangChain
- ChromaDB
- Pydantic Settings
- MCP

## 启动

```bash
cd python-ai-service
pip install -r requirements.txt
python main.py
```

服务默认运行在 `http://127.0.0.1:8000`。

如果需要独立的 MCP 启动入口，可以运行：

```bash
python -m app.mcp_server
```

## 主要接口

- `GET /health`
- `GET /docs`
- `GET /api/mcp/tools`
- `POST /api/mcp/{tool_name}`
- `POST /api/knowledge/add`
- `POST /api/knowledge/upload`
- `GET /api/knowledge/search`
- `GET /api/knowledge/stats`
- `GET /api/knowledge/records`
- `POST /api/knowledge/records`
- `PUT /api/knowledge/records/{record_id}`
- `DELETE /api/knowledge/records/{record_id}`
- `POST /api/review`
- `POST /api/check-completeness`

## 说明

完整接口说明、请求参数和部署步骤请参考 [../API文档.md](../API文档.md) 与 [../部署说明.md](../部署说明.md)。