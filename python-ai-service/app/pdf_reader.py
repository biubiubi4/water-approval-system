from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import List, Optional

try:
    import fitz
except Exception:  # pragma: no cover - optional dependency
    fitz = None

try:
    from langchain.schema import Document
except ImportError:
    from langchain_core.documents import Document

from app.config import settings


def _get_dashscope_api_key() -> Optional[str]:
    return os.getenv("DASHSCOPE_API_KEY")


def _to_data_uri(image_bytes: bytes) -> str:
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def _extract_response_text(response: object) -> str:
    output = getattr(response, "output", None)
    if output is None and isinstance(response, dict):
        output = response.get("output")

    choices = getattr(output, "choices", None)
    if choices is None and isinstance(output, dict):
        choices = output.get("choices")

    if not choices:
        return ""

    first_choice = choices[0]
    message = getattr(first_choice, "message", None)
    if message is None and isinstance(first_choice, dict):
        message = first_choice.get("message")

    content = getattr(message, "content", None)
    if content is None and isinstance(message, dict):
        content = message.get("content")

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if text:
                    parts.append(str(text))
            else:
                text = getattr(item, "text", None)
                if text:
                    parts.append(str(text))
        return "\n".join(parts).strip()

    return str(content).strip() if content else ""


def _extract_pdf_page_with_qwen(page_image: bytes, file_name: str, page_number: int) -> str:
    api_key = _get_dashscope_api_key()
    if not api_key:
        print(f"[PDF解析] 未配置 DASHSCOPE_API_KEY，跳过 Qwen-VL 读取: {file_name} 第 {page_number} 页")
        return ""

    try:
        import dashscope
    except Exception as error:
        print(f"dashscope 不可用，无法调用 Qwen PDF 读取: {error}")
        return ""

    if api_key:
        try:
            dashscope.api_key = api_key
        except Exception:
            pass

    prompt = (
        "请读取这张PDF页面截图中的所有文字内容，并尽量保留表格结构。"
        "如果包含表格，请使用 Markdown 表格或用竖线分隔列；"
        "如果包含标题、段落、编号条款，也请按原始顺序输出。"
        "只输出可用于后续检索的纯文本，不要解释，不要添加多余前缀。"
    )

    try:
        print(
            "[PDF解析] 调用 Qwen-VL 读取PDF页面: "
            f"model={settings.pdf_reader_qwen_model}, file={file_name}, page={page_number}"
        )
        response = dashscope.MultiModalConversation.call(
            model=settings.pdf_reader_qwen_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"image": _to_data_uri(page_image)},
                        {"text": prompt},
                    ],
                }
            ],
        )
        text = _extract_response_text(response)
        if text.strip():
            print(f"[PDF解析] Qwen-VL 读取成功: {file_name} 第 {page_number} 页")
        else:
            print(f"[PDF解析] Qwen-VL 已返回但未提取到文本: {file_name} 第 {page_number} 页")
        return text
    except Exception as error:
        print(f"Qwen PDF 页面读取失败 {file_name} 第 {page_number} 页: {error}")
        return ""


def load_pdf_with_qwen(file_path: Path) -> List[Document]:
    if fitz is None:
        print("PyMuPDF 不可用，跳过 Qwen PDF 读取")
        return []

    try:
        document = fitz.open(str(file_path))
    except Exception as error:
        print(f"打开 PDF 失败 {file_path}: {error}")
        return []

    documents: List[Document] = []
    max_pages = min(len(document), max(1, int(settings.pdf_reader_max_pages)))
    zoom = float(settings.pdf_reader_render_zoom)
    matrix = fitz.Matrix(zoom, zoom)

    for page_index in range(max_pages):
        try:
            page = document.load_page(page_index)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image_bytes = pixmap.tobytes("png")
            text = _extract_pdf_page_with_qwen(image_bytes, file_path.name, page_index + 1)
            if not text.strip():
                continue

            documents.append(
                Document(
                    page_content=text.strip(),
                    metadata={
                        "source": file_path.name,
                        "file_path": str(file_path),
                        "page": page_index + 1,
                        "reader": "qwen-vl",
                    },
                )
            )
        except Exception as error:
            print(f"Qwen PDF 页面处理失败 {file_path} 第 {page_index + 1} 页: {error}")

    return documents
