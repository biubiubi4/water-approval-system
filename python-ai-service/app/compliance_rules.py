from __future__ import annotations

from typing import Any, Dict, List

from app.application_form_parser import get_field_value


COMPLIANCE_RULE_VERSION = "2026-07-13-compliance-dimensions-v1"


COMPLIANCE_DIMENSIONS = [
    {"code": "applicant_identity", "name": "申请主体与身份信息"},
    {"code": "application_form", "name": "标准申请书关键栏目"},
    {"code": "water_source", "name": "水源与取水地点"},
    {"code": "water_quantity", "name": "取水量与期限"},
    {"code": "water_use", "name": "取水用途"},
    {"code": "metering", "name": "计量方式"},
    {"code": "drainage", "name": "退水与排放去向"},
    {"code": "commitment", "name": "承诺与签章"},
    {"code": "legal_restriction", "name": "法规限制性条款"},
]


RESTRICTIVE_KEYWORDS = ["禁止", "不得", "限制", "不予批准", "保护区", "管控"]


def evaluate_compliance_dimensions(
    application: Dict[str, Any] | None,
    knowledge_hits: List[Dict[str, Any]] | None = None,
    application_form_fields: Dict[str, Any] | None = None,
    rag_evidence: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    app = application if isinstance(application, dict) else {}
    fields = application_form_fields if isinstance(application_form_fields, dict) else {}
    evidence = rag_evidence if isinstance(rag_evidence, dict) else {}
    dimensions = [_dimension(item["code"], item["name"], evidence.get(item["code"])) for item in COMPLIANCE_DIMENSIONS]
    by_code = {item["code"]: item for item in dimensions}

    _check_applicant_identity(app, fields, by_code["applicant_identity"])
    _check_application_form(app, fields, by_code["application_form"])
    _check_water_source(app, fields, by_code["water_source"])
    _check_water_quantity(app, fields, by_code["water_quantity"])
    _check_water_use(app, fields, by_code["water_use"])
    _check_metering(app, fields, by_code["metering"])
    _check_drainage(app, fields, by_code["drainage"])
    _check_commitment(fields, by_code["commitment"])
    _check_legal_restrictions(knowledge_hits or [], evidence, by_code["legal_restriction"])

    for item in dimensions:
        item["status"] = _dimension_status(item)

    blockers = _collect_messages(dimensions, "BLOCKER")
    warnings = _collect_messages(dimensions, "WARNING")
    overall_status = "FAIL" if blockers else "WARNING" if warnings else "PASS"

    return {
        "pass": not blockers,
        "status": overall_status,
        "rule_version": COMPLIANCE_RULE_VERSION,
        "dimensions": dimensions,
        "violations": blockers,
        "warnings": warnings,
        "suggestions": _collect_suggestions(dimensions),
    }


def build_dimension_queries(application: Dict[str, Any] | None, application_form_fields: Dict[str, Any] | None = None) -> Dict[str, str]:
    app = application if isinstance(application, dict) else {}
    fields = application_form_fields if isinstance(application_form_fields, dict) else {}
    location = get_field_value(app, fields, "location", "intake_location") or "取水地点"
    water_use = get_field_value(app, fields, "water_use") or "取水用途"
    quantity = get_field_value(app, fields, "annual_water_quantity", "operation_annual_quantity") or "取水量"
    drainage = get_field_value(app, fields, "drainage_method") or "退水排放去向"

    return {
        "water_source": f"{location} 保护区 取水许可 禁止",
        "water_use": f"{water_use} 取水许可 限制 用途",
        "water_quantity": f"{quantity} 水资源论证 管控指标 取水许可",
        "drainage": f"{drainage} 水功能区 退水 排放 取水许可",
        "metering": "取水 计量设施 计量方式 数据传输 管理要求",
        "legal_restriction": f"{location} {water_use} 禁止 不得 不予批准 限制 取水许可",
    }


def summarize_rag_evidence(rag_evidence: Dict[str, Any] | None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    for code, item in (rag_evidence or {}).items():
        hits = item.get("hits") if isinstance(item, dict) else []
        payload[code] = [
            {
                "source": hit.get("source"),
                "content": str(hit.get("content") or "")[:180],
                "score": hit.get("score") or hit.get("similarity"),
            }
            for hit in hits or []
        ]
    return payload


def has_restrictive_evidence(rag_evidence: Dict[str, Any] | None) -> bool:
    for item in (rag_evidence or {}).values():
        for hit in item.get("hits", []) if isinstance(item, dict) else []:
            if _contains_restriction(str(hit.get("content") or "")):
                return True
    return False


def _dimension(code: str, name: str, evidence: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return {
        "code": code,
        "name": name,
        "status": "PASS",
        "findings": [],
        "evidence": (evidence or {}).get("hits", []),
        "suggestions": [],
    }


def _check_applicant_identity(app: Dict[str, Any], fields: Dict[str, Any], dimension: Dict[str, Any]) -> None:
    applicant = get_field_value(app, fields, "applicant_name")
    applicant_id = get_field_value(app, fields, "applicant_id")
    if not applicant:
        _add_finding(dimension, "WARNING", "未能识别申请主体名称，建议复核申请书和主体资格材料")
    if not applicant_id:
        _add_finding(dimension, "WARNING", "未能识别证件号或统一社会信用代码，建议复核主体资格材料")


def _check_application_form(app: Dict[str, Any], fields: Dict[str, Any], dimension: Dict[str, Any]) -> None:
    required = [
        ("project_name", "项目名称"),
        ("water_use", "取水用途"),
        ("location", "取水地点"),
    ]
    missing = [label for code, label in required if not get_field_value(app, fields, code)]
    if missing:
        _add_finding(dimension, "WARNING", f"标准申请书关键栏目缺少或未识别：{'、'.join(missing)}")


def _check_water_source(app: Dict[str, Any], fields: Dict[str, Any], dimension: Dict[str, Any]) -> None:
    if not get_field_value(app, fields, "location", "intake_location"):
        _add_finding(dimension, "WARNING", "取水地点或取水口位置缺少明确说明")
    if not get_field_value(app, fields, "water_source_type"):
        _add_finding(dimension, "WARNING", "水源类型未明确，建议补充地表水、地下水或其他水源类型")


def _check_water_quantity(app: Dict[str, Any], fields: Dict[str, Any], dimension: Dict[str, Any]) -> None:
    if not get_field_value(app, fields, "annual_water_quantity", "operation_annual_quantity", "construction_water_quantity"):
        _add_finding(dimension, "WARNING", "未识别年取水量或施工期取水量")
    if not get_field_value(app, fields, "term"):
        _add_finding(dimension, "WARNING", "取水期限未明确")


def _check_water_use(app: Dict[str, Any], fields: Dict[str, Any], dimension: Dict[str, Any]) -> None:
    water_use = get_field_value(app, fields, "water_use")
    detail = get_field_value(app, fields, "water_use_detail", "other_water_use", "water_use_description")
    if not water_use:
        _add_finding(dimension, "WARNING", "取水用途未明确")
    if water_use in {"其他", "其它"} and not detail:
        _add_finding(dimension, "BLOCKER", "取水用途选择“其他”时，必须填写具体用途说明")
    if "饮用水" in water_use:
        _add_finding(dimension, "WARNING", "取水用途涉及饮用水，需结合水源保护区和法规条款复核")


def _check_metering(app: Dict[str, Any], fields: Dict[str, Any], dimension: Dict[str, Any]) -> None:
    if not get_field_value(app, fields, "metering_method"):
        _add_finding(dimension, "WARNING", "计量方式或计量设施未明确")


def _check_drainage(app: Dict[str, Any], fields: Dict[str, Any], dimension: Dict[str, Any]) -> None:
    has_quantity = bool(get_field_value(app, fields, "return_water_quantity"))
    has_method = bool(get_field_value(app, fields, "drainage_method"))
    if not has_quantity and not has_method:
        _add_finding(dimension, "WARNING", "年退水量、退水方式或排放去向未明确")


def _check_commitment(fields: Dict[str, Any], dimension: Dict[str, Any]) -> None:
    if not get_field_value({}, fields, "commitment"):
        _add_finding(dimension, "WARNING", "未识别申请承诺内容或签章信息")


def _check_legal_restrictions(
    knowledge_hits: List[Dict[str, Any]],
    rag_evidence: Dict[str, Any],
    dimension: Dict[str, Any],
) -> None:
    hits = list(knowledge_hits)
    for item in rag_evidence.values():
        if isinstance(item, dict):
            hits.extend(item.get("hits") or [])

    restrictive_hits = [hit for hit in hits if _contains_restriction(str(hit.get("content") or ""))]
    if restrictive_hits:
        _add_finding(dimension, "WARNING", "知识库命中禁止、限制或保护区相关条款，建议进入法规适用复核")


def _contains_restriction(content: str) -> bool:
    return any(keyword in content for keyword in RESTRICTIVE_KEYWORDS)


def _add_finding(dimension: Dict[str, Any], severity: str, message: str) -> None:
    dimension["findings"].append({"severity": severity, "message": message})
    if severity == "BLOCKER":
        dimension["suggestions"].append(message)
    elif severity == "WARNING":
        dimension["suggestions"].append(f"建议复核：{message}")


def _dimension_status(dimension: Dict[str, Any]) -> str:
    severities = {item.get("severity") for item in dimension.get("findings", [])}
    if "BLOCKER" in severities:
        return "BLOCKER"
    if "WARNING" in severities:
        return "WARNING"
    return "PASS"


def _collect_messages(dimensions: List[Dict[str, Any]], severity: str) -> List[str]:
    messages: List[str] = []
    for dimension in dimensions:
        for finding in dimension.get("findings", []):
            if finding.get("severity") == severity:
                messages.append(f"{dimension['name']}：{finding.get('message')}")
    return messages


def _collect_suggestions(dimensions: List[Dict[str, Any]]) -> List[str]:
    suggestions: List[str] = []
    for dimension in dimensions:
        suggestions.extend(str(item) for item in dimension.get("suggestions", []) if item)
    return suggestions
