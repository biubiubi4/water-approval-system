# Handoff: 维度化合规审查升级

更新时间：2026-07-13

## 本轮完成内容

本轮根据 `会话工作总结与合规升级计划.md` 继续推进“合规维度清单 + RAG 条款依据 + Qwen 复核”的升级，已完成后端主流程接入和前端兼容展示。

### 1. 后端合规规则结构化

新增 `python-ai-service/app/compliance_rules.py`，将原先较薄的 `_check_compliance()` 升级为维度化合规判断。

当前合规维度包括：

- `applicant_identity`：申请主体与身份信息
- `application_form`：标准申请书关键栏目
- `water_source`：水源与取水地点
- `water_quantity`：取水量与期限
- `water_use`：取水用途
- `metering`：计量方式
- `drainage`：退水与排放去向
- `commitment`：承诺与签章
- `legal_restriction`：法规限制性条款

输出结构包含：

- `pass`
- `status`
- `rule_version`
- `dimensions`
- `violations`
- `warnings`
- `suggestions`

其中 `BLOCKER` 会进入 `violations`，可直接驳回；`WARNING` 仅表示需复核，不单独导致驳回。

### 2. 申请书字段轻量抽取

新增 `python-ai-service/app/application_form_parser.py`，在附件解析后从申请书文本中抽取关键字段。

抽取结果写入：

```json
{
  "details": {
    "application_form_fields": {}
  }
}
```

目前支持申请主体、证件号、法定代表人、项目名称、水源类型、取水地点、取水量、取水用途、计量方式、退水方式、承诺内容等字段的轻量正则抽取。

### 3. Agent 审核流程接入

修改 `python-ai-service/app/agent.py`：

- 附件解析后生成 `details.application_form_fields`
- 按合规维度构造 RAG query
- 将维度检索结果写入 `details.rag_evidence`
- 将本地合规结果写入 `details.compliance`
- 本地 `BLOCKER` 命中时跳过 Qwen，直接按本地结果驳回
- `WARNING` 不再单独导致驳回
- `ai_review_trace` 新增 `compliance_rule_version`

当前结果结构重点为：

```json
{
  "details": {
    "fast_rules": {},
    "completeness": {},
    "application_form_fields": {},
    "rag_evidence": {},
    "compliance": {
      "pass": true,
      "status": "PASS",
      "dimensions": [],
      "violations": [],
      "warnings": []
    },
    "external_ai": {},
    "ai_review_trace": {}
  }
}
```

### 4. Qwen 结构化复核约束

修改 `python-ai-service/app/llm_client.py`：

- Prompt 明确要求 Qwen 输出 JSON
- `details.compliance` 固定包含 `pass`、`status`、`dimensions`、`violations`、`suggestions`
- 每个 AI 维度项固定包含 `code`、`status`、`reason`、`legal_basis`
- 将本地维度化初判和按维度 RAG 证据传入 Qwen
- 明确要求本地 `BLOCKER` 不得被改判为通过
- 增加外部 AI 合规结构的归一化处理

### 5. 前端展示升级

修改：

- `frontend/src/components/ReviewResult.vue`
- `frontend/src/components/ApplicationDetails.vue`

新增展示：

- 合规维度列表
- 维度状态：通过、需复核、硬性问题、不通过
- 维度 findings 或 AI reason
- 按维度法规依据
- 申请书字段识别结果
- 合规性判断中区分“通过 / 有风险需复核 / 不通过”

旧审核结果没有新字段时仍按原逻辑兼容展示。

## 已验证内容

本轮未启动项目，仅做基础测试和构建检查。

已执行并通过：

```bash
python -m compileall python-ai-service/app
```

```bash
npm run build
```

还执行了一个轻量 Python 用例，确认 `evaluate_compliance_dimensions()` 可返回 `PASS` 且生成 9 个维度。

## Git 状态说明

本轮业务改动已在上一轮按用户要求提交并推送：

```text
1a6e5e0 升级维度化合规审查流程
```

本次仅新增本交接文档 `handoff.md`，按当前用户要求：

- 不提交
- 不推送

当前仍存在两个既有未提交 Java 编译产物变更，未纳入业务提交：

```text
java-backend/target/classes/com/waterapproval/config/WebConfig$1.class
java-backend/target/classes/com/waterapproval/config/WebConfig.class
```

这两个文件属于 `target/classes` 编译输出，不是本轮业务源码变更，后续提交时建议继续排除。

## 后续建议

1. 如需继续增强，应优先完善 `compliance_rules.py` 的维度规则，例如取水量格式、退水场景、计量设施必填条件。
2. RAG 目前已按维度检索，但 `details.rag_evidence` 为摘要结构；如前端需要可追溯详情，可保留更多 `metadata`、`page`、`chunk`。
3. 申请书字段抽取目前是轻量正则，适合兜底；若申请书格式稳定，可进一步按表格结构或模板字段解析。
4. Qwen 输出已加 JSON 约束，但实际线上仍需观察失败率和非 JSON 回退情况。
5. 前端已兼容新旧结果，但可进一步拆出独立 `ComplianceDimensions` 组件，减少两个页面的重复展示逻辑。
