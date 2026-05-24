from __future__ import annotations

from typing import Any, Dict

from app.mcp_tools import MCP_TOOLS, execute_tool

try:
    from mcp.server.fastmcp import FastMCP
except Exception:  # pragma: no cover - optional dependency
    FastMCP = None


def create_server():
    if FastMCP is None:
        raise RuntimeError("未安装 mcp 依赖，请先执行 pip install -r requirements.txt")

    server = FastMCP("Water Approval AI Service")

    @server.tool()
    def knowledge_search(query: str, top_k: int = 4) -> Dict[str, Any]:
        return execute_tool("knowledge_search", {"query": query, "top_k": top_k})

    @server.tool()
    def check_completeness(application: Dict[str, Any] | None = None, materials: list[str] | None = None) -> Dict[str, Any]:
        return execute_tool(
            "check_completeness",
            {"application": application or {}, "materials": materials or []},
        )

    return server


def main() -> None:
    server = create_server()
    server.run()


if __name__ == "__main__":
    main()