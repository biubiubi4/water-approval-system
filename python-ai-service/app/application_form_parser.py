from __future__ import annotations

import re
from typing import Any, Dict, List


FIELD_PATTERNS = {
    "applicant_name": ["申请人", "申请单位", "取水单位"],
    "applicant_id": ["统一社会信用代码", "身份证号码", "证件号码", "证件号"],
    "legal_representative": ["法定代表人", "负责人"],
    "project_name": ["项目名称"],
    "project_type": ["项目性质"],
    "project_summary": ["项目概况", "项目基本情况"],
    "operation_annual_quantity": ["运行期年取水量", "运行期取水量"],
    "water_source_type": ["水源类型", "取水水源"],
    "location": ["取水地点"],
    "intake_location": ["取水口位置", "取水口坐标"],
    "annual_water_quantity": ["年取水量", "申请年取水量"],
    "construction_water_quantity": ["施工期取水量"],
    "water_project_type": ["取水工程类型", "取水工程"],
    "application_reason": ["申请事由", "申请理由"],
    "start_date": ["申请取水起始时间", "取水起始时间", "开始取水时间"],
    "term": ["期限", "取水期限"],
    "water_use": ["取水用途", "用水用途"],
    "metering_method": ["计量方式", "计量设施", "计量方法"],
    "return_water_quantity": ["年退水量", "退水量"],
    "drainage_method": ["退水方式", "排放去向", "退水方式和排放去向"],
    "commitment": ["承诺内容", "申请人承诺", "承诺"],
}


def parse_application_form_fields(documents: List[Any] | None = None) -> Dict[str, Any]:
    text = _join_document_text(documents or [])
    if not text:
        return {}

    fields: Dict[str, Any] = {}
    for code, labels in FIELD_PATTERNS.items():
        value = _extract_field_value(text, labels)
        if value:
            fields[code] = {
                "value": value,
                "source": "attachment_text",
                "labels": labels,
            }

    return fields


def get_field_value(
    application: Dict[str, Any] | None,
    fields: Dict[str, Any] | None,
    *names: str,
) -> str:
    app = application if isinstance(application, dict) else {}
    parsed = fields if isinstance(fields, dict) else {}

    for name in names:
        value = app.get(name)
        if _has_value(value):
            return str(value).strip()

    for name in names:
        item = parsed.get(name)
        if isinstance(item, dict) and _has_value(item.get("value")):
            return str(item.get("value")).strip()
        if _has_value(item):
            return str(item).strip()

    return ""


def extract_field_value_from_text(text: str, labels: List[str]) -> str:
    return _extract_field_value(text, labels)


def _join_document_text(documents: List[Any]) -> str:
    parts: List[str] = []
    for document in documents:
        text = str(getattr(document, "page_content", "") or "").strip()
        if text:
            parts.append(text)
    return "\n".join(parts)


def _extract_field_value(text: str, labels: List[str]) -> str:
    for label in labels:
        escaped_label = re.escape(label)
        patterns = [
            rf"{escaped_label}\s*[：:]\s*([^\n\r；;。]{{1,120}})",
            rf"{escaped_label}\s+([^\n\r；;。]{{1,120}})",
            rf"{escaped_label}[^\n\r：:]{{0,8}}[：:]\s*([^\n\r；;。]{{1,120}})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                value = _clean_value(match.group(1))
                if value:
                    return value
    return ""


def _clean_value(value: str) -> str:
    value = re.sub(r"\s+", " ", str(value or "")).strip(" ：:\t\r\n")
    value = re.split(r"\s{2,}", value)[0].strip()
    return value[:120]


def _has_value(value: Any) -> bool:
    return str(value or "").strip() not in {"", "无", "暂无", "待补充", "未填写", "none", "null", "n/a"}
