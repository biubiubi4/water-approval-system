from __future__ import annotations

import re
from datetime import date
from typing import Any, Dict, Iterable, List


RULE_VERSION = "2026-07-13-standard-application-form-v3"


REQUIRED_FIELDS = [
    {"name": "applicant_name", "label": "申请人或申请单位", "document_labels": ["申请人", "申请人（盖章）"]},
    {"name": "applicant_id", "label": "证件号或统一社会信用代码", "document_labels": ["统一社会信用代码", "身份证号码"]},
    {"name": "project_name", "label": "项目名称", "document_labels": ["项目名称"]},
    {"name": "water_use", "label": "取水用途", "document_labels": ["取水用途"]},
    {"name": "location", "label": "取水地点", "document_labels": ["取水地点", "取水口位置"]},
]


REQUIRED_MATERIAL_GROUPS = [
    {
        "name": "取水许可申请书",
        "severity": "BLOCKER",
        "aliases": ["取水许可申请书", "取水申请书", "申请书", "申请表", "water application form"],
        "document_keywords": ["取水许可申请书", "取水许可申请", "申请人基本情况", "项目基本情况", "运行期年取水量"],
    },
    {
        "name": "身份证或营业执照",
        "severity": "BLOCKER",
        "aliases": ["身份证", "身份证明", "营业执照", "统一社会信用代码", "主体资格", "法人证书", "信用代码证"],
        "document_keywords": ["营业执照", "居民身份证", "中华人民共和国居民身份证", "法定代表人身份证"],
    },
]


PLACEHOLDER_VALUES = {"", "无", "暂无", "待补充", "未填写", "空", "none", "null", "n/a"}


def normalize_text(value: Any) -> str:
    return str(value or "").strip().lower()


def compact_text(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).lower()


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


def match_material_group_in_text(group: Dict[str, Any], document_text: str) -> bool:
    text = compact_text(document_text)
    if not text:
        return False

    for keyword in group.get("document_keywords", []):
        if compact_text(keyword) in text:
            return True
    return False


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
        _check_required_fields(app, issues, document_text)
    _check_required_materials(material_names, issues, document_text, has_document_items=bool(document_items))
    _check_application_form_rules(app, issues, document_text)

    if document_items:
        _check_attachment_type_consistency(document_items, issues)
        _check_expiration_dates(document_items, issues)
        _check_application_document_consistency(app, document_text, issues)

    blockers = [issue for issue in issues if issue["severity"] == "BLOCKER"]
    warnings = [issue for issue in issues if issue["severity"] == "WARNING"]
    status = "BLOCKER" if blockers else "WARNING" if warnings else "PASS"

    return {
        "rule_version": RULE_VERSION,
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


def build_completeness_from_rules(
    rule_result: Dict[str, Any],
    submitted_materials: List[str] | None = None,
) -> Dict[str, Any]:
    blockers = [
        issue for issue in rule_result.get("issues", [])
        if issue.get("severity") == "BLOCKER"
    ]
    missing_items = [
        str(issue.get("message", "")).removeprefix("缺少材料：")
        for issue in blockers
        if str(issue.get("code", "")).startswith("missing_material_")
    ]
    missing_fields = [
        str(issue.get("field"))
        for issue in blockers
        if str(issue.get("code", "")).startswith("missing_field_") and issue.get("field")
    ]
    issues = [str(issue.get("message")) for issue in blockers if issue.get("message")]

    complete = len(blockers) == 0
    return {
        "complete": complete,
        "status": "PASS" if complete else "FAIL",
        "rule_version": rule_result.get("rule_version", RULE_VERSION),
        "submitted_materials": submitted_materials if submitted_materials is not None else rule_result.get("submitted_materials", []),
        "required_checklist": rule_result.get("required_materials", []),
        "matched_items": _matched_required_materials(
            submitted_materials if submitted_materials is not None else rule_result.get("submitted_materials", []),
            rule_result.get("required_materials", []),
        ),
        "missing_items": missing_items,
        "missing_fields": missing_fields,
        "issues": issues,
        "warnings": [issue.get("message") for issue in rule_result.get("warnings", []) if issue.get("message")],
        "fast_rules": rule_result,
    }


def _matched_required_materials(submitted_materials: List[str], required_materials: List[str]) -> List[str]:
    matched: List[str] = []
    for group in REQUIRED_MATERIAL_GROUPS:
        name = group["name"]
        if name not in required_materials:
            continue
        if match_material_group(group, submitted_materials):
            matched.append(name)
    return matched


def _check_required_fields(application: Dict[str, Any], issues: List[Dict[str, Any]], document_text: str = "") -> None:
    for field in REQUIRED_FIELDS:
        value = normalize_text(application.get(field["name"]))
        if value in PLACEHOLDER_VALUES and not _document_has_field(field, document_text):
            severity = "BLOCKER"
            if not document_text and field["name"] in {"project_name", "water_use", "location"}:
                severity = "WARNING"
            _add_issue(
                issues,
                code=f"missing_field_{field['name']}",
                severity=severity,
                message=f"缺少必填字段：{field['label']}",
                field=field["name"],
            )


def _document_has_field(field: Dict[str, Any], document_text: str) -> bool:
    text = compact_text(document_text)
    if not text:
        return False
    return any(compact_text(label) in text for label in field.get("document_labels", []))


def _check_required_materials(
    material_names: List[str],
    issues: List[Dict[str, Any]],
    document_text: str = "",
    has_document_items: bool = False,
) -> None:
    if not material_names:
        _add_issue(
            issues,
            code="missing_attachments",
            severity="BLOCKER",
            message="未上传任何附件材料",
        )
        return

    for group in REQUIRED_MATERIAL_GROUPS:
        if not match_material_group(group, material_names) and not match_material_group_in_text(group, document_text):
            if not has_document_items:
                severity = "WARNING"
            else:
                severity = str(group.get("severity", "WARNING"))
            _add_issue(
                issues,
                code=f"missing_material_{group['name']}",
                severity=severity,
                message=f"缺少材料：{group['name']}",
            )


def _check_application_form_rules(
    application: Dict[str, Any],
    issues: List[Dict[str, Any]],
    document_text: str = "",
) -> None:
    water_use = str(application.get("water_use") or "").strip()
    other_detail = str(
        application.get("water_use_detail")
        or application.get("other_water_use")
        or application.get("water_use_description")
        or ""
    ).strip()
    document_compact = compact_text(document_text)
    document_selects_other = any(
        marker in document_compact
        for marker in ["√其他用水", "☑其他用水", "√其他", "☑其他"]
    )
    document_has_other_detail = bool(re.search(r"(其他用水|其他)[^。；;\n（）()]{0,20}[：:（(]\s*[\u4e00-\u9fffA-Za-z0-9]{2,}", document_text))

    if (water_use in {"其他", "其它"} and not other_detail) or (document_selects_other and not document_has_other_detail):
        _add_issue(
            issues,
            code="missing_other_water_use_detail",
            severity="BLOCKER",
            message="取水用途选择“其他”时，必须填写具体用途说明",
            field="water_use",
        )


def _check_attachment_type_consistency(document_items: List[Dict[str, str]], issues: List[Dict[str, Any]]) -> None:
    grouped_items: Dict[str, List[str]] = {}
    for item in document_items:
        grouped_items.setdefault(item["source"], []).append(item["text"])

    for source, texts in grouped_items.items():
        source_text = normalize_text(source)
        content = normalize_text("\n".join(texts))
        compact_content = compact_text(content)

        if "身份证" in source_text and "驾驶证" in content and "身份证" not in content:
            _add_issue(
                issues,
                code="identity_attachment_type_mismatch",
                severity="BLOCKER",
                message=f"附件“{source}”名称疑似身份证，但解析内容显示为驾驶证",
                source=source,
            )

        if "营业执照" in source_text and not any(
            compact_text(key) in compact_content for key in ["营业执照", "统一社会信用代码", "营业期限"]
        ):
            _add_issue(
                issues,
                code="business_license_content_mismatch",
                severity="WARNING",
                message=f"附件“{source}”名称疑似营业执照，但解析文本缺少营业执照关键内容",
                source=source,
            )

        if any(key in source_text for key in ["申请书", "申请表"]) and not any(
            compact_text(key) in compact_content
            for key in ["取水许可", "取水申请", "申请人", "申请单位", "申请人基本情况", "项目基本情况"]
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
