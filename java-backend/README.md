# Java Backend

Spring Boot 主后端，用于承接前端申请管理接口，并调用 Python AI 服务完成初审。

## 启动

```bash
cd java-backend
mvn spring-boot:run
```

默认监听 `http://localhost:8080`。

## 接口

- `GET /api/applications`
- `GET /api/applications/{id}`
- `POST /api/applications`
- `POST /api/applications/{id}/review`

## 配置

Python AI 服务地址默认是 `http://127.0.0.1:8000`，可通过环境变量 `AI_SERVICE_BASE_URL` 覆盖。