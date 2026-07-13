# Architecture Diagram

本文展示涉水审批智能审核系统的总体架构与核心组件关系。系统采用 Vue 前端、Spring Boot 主后端和 Python AI 服务协作的双栈模式，覆盖申请管理、材料审查、知识检索与合规初审。

## Application Architecture

![Application Architecture](../../../../../assets/diagrams/architecture-diagram.svg)

### Technology Stack Summary

| Layer | Technology | Version | Purpose |
| --- | --- | --- | --- |
| Presentation | Vue | 3 | 单页前端界面和页面切换 |
| Build Tooling | Vite | 5 | 前端开发和打包 |
| Business Layer | Spring Boot | 3.2.5 | 申请管理和审核流程编排 |
| AI Service | FastAPI, LangChain | Current project stack | 知识检索、完整性检查和审核推理 |
| Vector Store | Chroma | Current project stack | 语义检索与知识库存储 |
| Data Storage | MySQL | 8 | 申请业务数据持久化 |
| File Storage | Local uploads directory | N/A | 附件文件保存 |

### Data Storage & External Services

系统的业务数据由 Java 后端写入 MySQL，附件文件保存在本地 uploads 目录，Python AI 服务使用 Chroma 维护知识向量索引，并从法规和知识文件中完成检索与审核推理。前端不直接访问数据库，而是统一通过后端 REST API 完成数据读取和提交。

### Key Architectural Decisions

- 前端、业务后端和 AI 服务相互独立，便于分别演进和部署。
- 审核结果由 Python AI 服务生成，再回写到 Java 后端统一保存和展示。
- 附件采用本地文件系统配合数据库元数据的方式管理，降低了上传和回显的复杂度。

## Component Relationships

![Component Relationships](../../../../../assets/diagrams/architecture-diagram.svg)

### Component Inventory

| Component | Layer | Type | Responsibility |
| --- | --- | --- | --- |
| App.vue | Presentation | Page shell | 维护当前页面状态并驱动页面切换 |
| ApplicationList.vue | Presentation | List page | 展示申请列表、搜索、删除和进入详情或审核 |
| CreateApplication.vue | Presentation | Form page | 创建或编辑申请并上传附件 |
| ReviewResult.vue | Presentation | Result page | 展示审核结果并支持重新审核 |
| ApplicationDetails.vue | Presentation | Detail page | 展示申请信息、审核情况和附件 |
| KnowledgeManager.vue | Presentation | Knowledge page | 管理知识库、解析文件和语义检索 |
| ApplicationController | Business Logic | REST controller | 提供申请 CRUD 和审核接口 |
| KnowledgeController | Business Logic | REST controller | 提供知识库管理接口 |
| ApplicationService | Business Logic | Domain service | 编排申请保存、更新、审核和删除 |
| AiServiceClient | Business Logic | Integration client | 调用 Python AI 服务执行检索和审核 |
| ApplicationRepository | Data Access | Repository | 持久化申请数据 |
| WebConfig | Infrastructure | Web configuration | 提供跨域等 Web 层配置 |
| GlobalExceptionHandler | Infrastructure | Exception handler | 统一处理接口异常 |
| Python AI 服务 | Infrastructure | External service | 完成完整性检查、知识检索和审核推理 |
| Chroma 向量库 | Infrastructure | Vector store | 存储和检索知识向量 |
| MySQL 数据库 | Data Access | Relational database | 保存申请业务数据 |
