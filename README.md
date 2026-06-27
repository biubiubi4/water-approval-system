# 取水申请材料合规性检测系统

本项目是一个基于 Java + Python 双栈架构的涉水审批智能审核系统，用于对取水申请材料进行自动化完整性检查、知识库检索和合规性初审。

## 项目组成

- 前端：[frontend](frontend) ，Vue 3 + Vite，默认端口 3000
- Java 主后端：[java-backend](java-backend) ，Spring Boot 3.2.5，默认端口 8080
- Python AI 服务：[python-ai-service](python-ai-service) ，FastAPI + LangChain + Chroma，默认端口 8000

## 功能概览

- 申请管理：创建、查询、编辑、删除和审核申请
- 材料审查：根据申请类型检查申请书、身份证或营业执照等材料
- 知识库管理：上传、检索、维护法规和示例知识
- 智能审核：调用 Python AI 服务执行知识检索、完整性检查和审查结果生成

## 文档入口

- [API 文档](API文档.md)
- [部署说明](部署说明.md)
- [项目启动指南](项目启动指南.md)
- [系统设计文档说明书](系统设计文档说明书.md)
- [需求文档说明书](需求文档说明书.md)
- [团队分工文档](团队分工文档.md)

## 关键环境

- Java 17
- Maven 3.8+
- Python 3.9+
- Node.js 18+
- MySQL 8+

## 快速启动

1. 启动 Python AI 服务：进入 [python-ai-service](python-ai-service)，安装依赖后执行 `python main.py`
2. 启动 Java 后端：进入 [java-backend](java-backend)，执行 `mvn spring-boot:run`
3. 启动前端：进入 [frontend](frontend)，执行 `npm install` 和 `npm run dev`

## 说明

Java 后端通过环境变量 `AI_SERVICE_BASE_URL` 指向 Python AI 服务，默认值为 `http://127.0.0.1:8000`。Python 服务会自动初始化向量库和示例知识，支持本地规则审核与知识检索。
