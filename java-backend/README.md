# Java Backend

Spring Boot 主后端，负责申请管理、文件上传、知识库管理接口，并转发审核请求到 Python AI 服务。

## 技术栈

- Spring Boot 3.2.5
- Java 17
- Spring Web / Validation / JPA
- MySQL 8

## 启动

```bash
cd java-backend
mvn spring-boot:run
```

默认监听 `http://localhost:8080`。

## 主要接口

- `GET /api/applications`
- `GET /api/applications/{id}`
- `POST /api/applications`
- `PUT /api/applications/{id}`
- `DELETE /api/applications/{id}`
- `POST /api/applications/{id}/review`
- `GET /api/ai/tools`
- `GET /api/ai/knowledge/search`
- `POST /api/ai/review`
- `POST /api/ai/check-completeness`
- `GET /api/knowledge/stats`
- `GET /api/knowledge/records`

## 配置

- 数据库默认连接 `jdbc:mysql://localhost:3306/water_approval_db`
- 可通过 `SPRING_DATASOURCE_URL`、`spring.datasource.username`、`spring.datasource.password` 覆盖
- Python AI 服务地址默认是 `http://127.0.0.1:8000`，可通过 `AI_SERVICE_BASE_URL` 覆盖

## 说明

完整接口说明、请求体和返回值示例请参考 [../API文档.md](../API文档.md)；部署步骤请参考 [../部署说明.md](../部署说明.md)。