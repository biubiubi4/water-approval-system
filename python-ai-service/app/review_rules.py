from __future__ import annotations

import re
from datetime import date
from typing import Any, Dict, Iterable, List


REQUIRED_FIELDS = [
    {"name": "applicant_name", "label": "申请人或申请单位"},
    {"name": "applicant_id", "label": "证件号或统一社会信用代码"},
    {"name": "project_name", "label": "项目名称"},
    {"name": "water_use", "label": "取水用途"},
    {"name": "location", "label": "取水地点"},
]


REQUIRED_MATERIAL_GROUPS = [
    {
        "name": "取水许可申请书",
        "severity": "BLOCKER",
        "aliases": ["取水许可申请书", "取水申请书", "申请书", "申请表", "water application form"],
    },
    {
        "name": "身份证或营业执照",
        "severity": "BLOCKER",
        "aliases": ["身份证", "身份证明", "营业执照", "统一社会信用代码", "主体资格", "法人证书", "信用代码证"],
    },
    {
        "name": "水资源论证相关材料",
        "severity": "WARNING",
        "aliases": ["水资源论证", "论证报告", "取水论证", "水资源评价", "可研报告"],
    },
]


PLACEHOLDER_VALUES = {"", "无", "暂无", "待补充", "未填写", "空", "none", "null", "n/a"}


def normalize_text(value: Any) -> str:
    return str(value or "").strip().lower()


def collect_material_names(application: Dict[str, Any] | List[str] | None, materials: List[str] | None = None) -> List[str]:
    if materials:
        return [str(item) for item in materials if str(item).strip()]

    if isinstance(application, list):
        return [str(item) for item in application if str(item).strip()]

    if not isinstance(application, dict):
        return []

    collected: List[str] = []
    for key in ["attachments", "file_names", "files"]:
        value = application.get(key)
        if isinstance(value, list):
            collected.extend(str(item) for item in value if str(item).strip())

    for field in [
        "application_form",
        "id_proof",
        "subject_qualification",
        "relation_statement",
        "assessment_report",
        "project_materials",
    ]:
        value = application.get(field)
        if value:
            collected.append(str(value))

    return _unique_keep_order(collected)


def match_material_group(group: Dict[str, Any], material_names: Iterable[str]) -> bool:
    aliases = [group["name"], *group.get("aliases", [])]
    normalized_materials = [normalize_text(item) for item in material_names]
    return any(
        any(normalize_text(alias) in material for material in normalized_materials)
        for alias in aliases
    )


def evaluate_application_rules(
    application: Dict[str, Any] | None,
    documents: List[Any] | None = None,
    materials: List[str] | None = None,
    check_fields: bool = True,
) -> Dict[str, Any]:
    app = application if isinstance(application, dict) else {}
    material_names = collect_material_names(app, materials)
    document_items = _document_items(documents or [])
    document_text = "\n".join(item["text"] for item in document_items)

    issues: List[Dict[str, Any]] = []

    if check_fields:
        _check_required_fields(app, issues)
    _check_required_materials(material_names, issues)
    _check_application_form_rules(app, issues)

    if document_items:
        _check_attachment_type_consistency(document_items, issues)
        _check_expiration_dates(document_items, issues)
        _check_application_document_consistency(app, document_text, issues)

    blockers = [issue for issue in issues if issue["severity"] == "BLOCKER"]
    warnings = [issue for issue in issues if issue["severity"] == "WARNING"]
    status = "BLOCKER" if blockers else "WARNING" if warnings else "PASS"

    return {
        "status": status,
        "passed": not blockers,
        "should_block": bool(blockers),
        "should_use_external_ai": bool(warnings),
        "blockers": blockers,
        "warnings": warnings,
        "issues": issues,
        "suggestions": [issue["message"] for issue in issues],
        "submitted_materials": material_names,
        "required_fields": [field["name"] for field in REQUIRED_FIELDS],
        "required_materials": [group["name"] for group in REQUIRED_MATERIAL_GROUPS],
    }


def _check_required_fields(application: Dict[str, Any], issues: List[Dict[str, Any]]) -> None:
    for field in REQUIRED_FIELDS:
        value = normalize_text(application.get(field["name"]))
        if value in PLACEHOLDER_VALUES:
            _add_issue(
                issues,
                code=f"missing_field_{field['name']}",
                severity="BLOCKER",
                message=f"缺少必填字段：{field['label']}",
                field=field["name"],
            )


def _check_required_materials(material_names: List[str], issues: List[Dict[str, Any]]) -> None:
    if not material_names:
        _add_issue(
            issues,
            code="missing_attachments",
            severity="BLOCKER",
            message="未上传任何附件材料",
        )
        return

    for group in REQUIRED_MATERIAL_GROUPS:
        if not match_material_group(group, material_names):
            _add_issue(
                issues,
                code=f"missing_material_{group['name']}",
                severity=str(group.get("severity", "WARNING")),
                message=f"缺少材料：{group['name']}",
            )


def _check_application_form_rules(application: Dict[str, Any], issues: List[Dict[str, Any]]) -> None:
    water_use = str(application.get("water_use") or "").strip()
    other_detail = str(
        application.get("water_use_detail")
        or application.get("other_water_use")
        or application.get("water_use_description")
        or ""
    ).strip()
    if water_use in {"其他", "其它"} and not other_detail:
        _add_issue(
            issues,
            code="missing_other_water_use_detail",
            severity="BLOCKER",
            message="取水用途选择“其他”时，必须填写具体用途说明",
            field="water_use",
        )


def _check_attachment_type_consistency(document_items: List[Dict[str, str]], issues: List[Dict[str, Any]]) -> None:
    for item in document_items:
        source = item["source"]
        source_text = normalize_text(source)
        content = normalize_text(item["text"])

        if "身份证" in source_text and "驾驶证" in content and "身份证" not in content:
            _add_issue(
                issues,
                code="identity_attachment_type_mismatch",
                severity="BLOCKER",
                message=f"附件“{source}”名称疑似身份证，但解析内容显示为驾驶证",
                source=source,
            )

        if "营业执照" in source_text and not any(key in content for key in ["营业执照", "统一社会信用代码", "营业期限"]):
            _add_issue(
                issues,
                code="business_license_content_mismatch",
                severity="WARNING",
                message=f"附件“{source}”名称疑似营业执照，但解析文本缺少营业执照关键内容",
                source=source,
            )

        if any(key in source_text for key in ["申请书", "申请表"]) and not any(
            key in content for key in ["取水许可", "取水申请", "申请人", "申请单位"]
        ):
            _add_issue(
                issues,
                code="application_form_content_mismatch",
                severity="WARNING",
                message=f"附件“{source}”名称疑似申请书，但解析文本缺少取水申请关键内容",
                source=source,
            )


def _check_expiration_dates(document_items: List[Dict[str, str]], issues: List[Dict[str, Any]]) -> None:
    today = date.today()
    patterns = [
        re.compile(r"(?:有效期|有效期限|营业期限)[^。；;\n]{0,50}(?:至|到|-|—)\s*(\d{4})[年/-]?\s*(\d{1,2})?"),
        re.compile(r"(?:有效期至|有效期限至|营业期限至)\s*(\d{4})[年/-]?\s*(\d{1,2})?"),
    ]

    for item in document_items:
        for pattern in patterns:
            for match in pattern.finditer(item["text"]):
                year = int(match.group(1))
                month = int(match.group(2) or 12)
                if year < today.year or (year == today.year and month < today.month):
                    _add_issue(
                        issues,
                        code="expired_certificate",
                        severity="BLOCKER",
                        message=f"附件“{item['source']}”中识别到证件或资质有效期已过期：{year}年{month}月",
                        source=item["source"],
                    )


def _check_application_document_consistency(
    application: Dict[str, Any],
    document_text: str,
    issues: List[Dict[str, Any]],
) -> None:
    normalized_document = normalize_text(document_text)
    if not normalized_document:
        return

    applicant_name = str(application.get("applicant_name") or "").strip()
    if applicant_name and applicant_name not in document_text:
        _add_issue(
            issues,
            code="applicant_name_not_found_in_documents",
            severity="WARNING",
            message="附件解析文本中未找到申请人或申请单位名称，建议复核申请数据与附件是否一致",
            field="applicant_name",
        )

    applicant_id = re.sub(r"\s+", "", str(application.get("applicant_id") or ""))
    if applicant_id and applicant_id.lower() not in normalized_document:
        _add_issue(
            issues,
            code="applicant_id_not_found_in_documents",
            severity="WARNING",
            message="附件解析文本中未找到证件号或统一社会信用代码，建议复核申请数据与附件是否一致",
            field="applicant_id",
        )


def _document_items(documents: List[Any]) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    for document in documents:
        metadata = getattr(document, "metadata", {}) or {}
        source = str(metadata.get("source") or metadata.get("file_path") or "附件")
        text = str(getattr(document, "page_content", "") or "")
        if text.strip():
            items.append({"source": source, "text": text})
    return items


def _add_issue(
    issues: List[Dict[str, Any]],
    code: str,
    severity: str,
    message: str,
    **extra: Any,
) -> None:
    payload = {
        "code": code,
        "severity": severity,
        "message": message,
    }
    payload.update({key: value for key, value in extra.items() if value is not None})
    issues.append(payload)


def _unique_keep_order(values: List[str]) -> List[str]:
    seen = set()
    unique: List[str] = []
    for value in values:
        key = value.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(value)
    return unique
