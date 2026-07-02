# API 文档

本文档描述涉水审批智能审核系统中 Java 后端与 Python AI 服务的主要接口。当前系统采用前后端分离架构，Java 后端负责业务流转与持久化，Python AI 服务负责知识检索、完整性检查与审查推理。

## 一、整体约定

- Java 后端默认地址：`http://localhost:8080`
- Python AI 服务默认地址：`http://localhost:8000`
- 前端默认地址：`http://localhost:3000`
- 目前接口无登录鉴权，适合内网或开发环境部署
- 申请上传接口使用 `multipart/form-data`
- AI 审核接口以 JSON 为主

## 二、Java 后端接口

### 2.1 申请管理

#### 获取申请列表

- 方法：`GET`
- 路径：`/api/applications`

返回：申请列表数组。

#### 获取申请详情

- 方法：`GET`
- 路径：`/api/applications/{id}`

返回：单条申请详情。

#### 新建申请

- 方法：`POST`
- 路径：`/api/applications`
- 类型：`multipart/form-data`

字段通常包括：

- `applicantName`
- `applicantId`
- `projectName`
- `waterUse`
- `location`
- `applicantType`
- `attachments`
- `files`

说明：`files` 为可选附件列表，支持多文件上传。

#### 更新申请

- 方法：`PUT`
- 路径：`/api/applications/{id}`
- 类型：`multipart/form-data`

说明：字段与新建申请一致。

#### 删除申请

- 方法：`DELETE`
- 路径：`/api/applications/{id}`

#### 触发审核

- 方法：`POST`
- 路径：`/api/applications/{id}/review`

返回：审核结果对象，包含完整性结论、合规性结论和建议信息。

### 2.2 AI 代理接口

#### 工具列表

- 方法：`GET`
- 路径：`/api/ai/tools`

返回：Python AI 服务暴露的 MCP 工具列表。

#### 知识检索

- 方法：`GET`
- 路径：`/api/ai/knowledge/search`
- 参数：`q`、`topK`

示例：`/api/ai/knowledge/search?q=取水许可&topK=4`

#### 智能审核

- 方法：`POST`
- 路径：`/api/ai/review`
- 请求体：申请 JSON 对象

返回：Python AI 服务的审查结果。

#### 完整性检查

- 方法：`POST`
- 路径：`/api/ai/check-completeness`
- 请求体：

```json
{
  "application": {},
  "materials": []
}
```

### 2.3 知识库管理

#### 统计信息

- 方法：`GET`
- 路径：`/api/knowledge/stats`

#### 知识记录列表

- 方法：`GET`
- 路径：`/api/knowledge/records`
- 参数：`q`、`source`、`record_type`

#### 获取知识记录

- 方法：`GET`
- 路径：`/api/knowledge/records/{recordId}`

#### 新建知识记录

- 方法：`POST`
- 路径：`/api/knowledge/records`

#### 更新知识记录

- 方法：`PUT`
- 路径：`/api/knowledge/records/{recordId}`

#### 删除知识记录

- 方法：`DELETE`
- 路径：`/api/knowledge/records/{recordId}`

#### 批量删除知识记录

- 方法：`POST`
- 路径：`/api/knowledge/records/batch-delete`

#### 删除知识文件

- 方法：`POST`
- 路径：`/api/knowledge/delete`

#### 按来源删除知识

- 方法：`POST`
- 路径：`/api/knowledge/delete-by-source`

## 三、Python AI 服务接口

Python 服务可以独立运行，也可以由 Java 后端间接调用。下列接口与 Java 转发接口语义一致。

### 3.1 健康与文档

- `GET /`
- `GET /health`
- `GET /docs`

### 3.2 MCP 工具

- `GET /api/mcp/tools`
- `POST /api/mcp/{tool_name}`

当前可用工具：

- `knowledge_search`
- `check_completeness`

### 3.3 知识库

- `POST /api/knowledge/add`
- `POST /api/knowledge/upload`
- `GET /api/knowledge/search?q=...&top_k=4`
- `GET /api/knowledge/stats`
- `GET /api/knowledge/records`
- `GET /api/knowledge/records/{record_id}`
- `POST /api/knowledge/records`
- `PUT /api/knowledge/records/{record_id}`
- `DELETE /api/knowledge/records/{record_id}`
- `POST /api/knowledge/delete`
- `POST /api/knowledge/delete-by-source`

### 3.4 审核接口

- `POST /api/review`
- `POST /api/check-completeness`

## 四、典型请求示例

### 4.1 材料完整性检查

```bash
curl -X POST http://localhost:8000/api/check-completeness ^
  -H "Content-Type: application/json" ^
  -d "{\"application\":{\"applicant_name\":\"张三\",\"applicant_type\":\"PERSONAL\",\"attachments\":[\"取水许可申请书\"]},\"materials\":[\"取水许可申请书\"]}"
```

### 4.2 智能审核

```bash
curl -X POST http://localhost:8000/api/review ^
  -H "Content-Type: application/json" ^
  -d "{\"application\":{\"applicant_name\":\"张三\",\"applicant_type\":\"ENTERPRISE\",\"attachments\":[\"取水许可申请书\",\"营业执照\"]}}"
```

### 4.3 知识库搜索

```bash
curl "http://localhost:8000/api/knowledge/search?q=取水许可&top_k=4"
```

## 五、返回值说明

### 5.1 完整性检查

常见字段包括：

- `complete`
- `applicant_type`
- `submitted_materials`
- `missing_items`
- `issues`

### 5.2 审核结果

常见字段包括：

- `reviewResult`
- `completeness`
- `compliance`
- `issues`
- `details`

## 六、兼容说明

- Python 服务默认使用本地规则和向量检索，不依赖外部大模型也可运行
- 若启用外部模型，可通过 Python 服务环境变量配置对应 provider 与 API key
- Java 后端通过 `AI_SERVICE_BASE_URL` 指向 Python 服务，默认值为 `http://127.0.0.1:8000`