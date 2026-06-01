# 取水申请材料合规性检测系统

## 项目简介
本系统是一个基于 **Java + Python 双栈架构**的**取水申请材料智能审核系统**，旨在利用 AI 技术实现对取水申请材料的**自动合规性审查**。
测试上传
## 项目背景
在涉水行政审批过程中，取水许可申请材料的审核工作繁重且专业性强。本系统通过：
- **形式审查**：检查申请材料是否齐全、格式是否正确
- **内容规范**：验证填写信息的一致性和完整性
- **实质合规**：对照水法等法规进行合规性判断
- **知识库检索**：基于向量数据库的语义检索

## 技术架构
- **前端**: Vue 3 + Vite (端口 3000)
- **主后端**: Java Spring Boot 3.x (端口 8080)
- **AI服务后端**: Python FastAPI + LangChain (端口 8000)
- **数据库**: H2 (内存数据库)
- **向量数据库**: ChromaDB

## 核心功能

### 1. MCP协议工具
- `knowledge_search` - 知识库搜索，检索取水相关法规
- `check_completeness` - 完整性检查，验证申请材料

### 2. LangChain Agent智能审核
- 材料完整性自动检查
- 法规知识库语义检索
- 合规性判断与建议
- 审核结果生成

### 3. 文档解析与知识库
- 支持 PDF、Word、TXT 文档解析
- Embedding 向量化存储
- 内置水法、取水许可条例等法规

### 4. 前端功能页面
- 申请列表页面 - 展示所有申请记录
- 新建申请页面 - 填写信息、上传附件
- 审核结果页面 - 查看详细审核意见

## 项目结构

```
water-approval-system/
├── java-backend/           # Java后端服务
│   ├── pom.xml            # Maven配置
│   └── src/main/java/com/waterapproval/
│       ├── WaterApprovalApplication.java
│       ├── controller/    # REST控制器
│       ├── service/       # 业务服务 + AI客户端
│       ├── dto/           # 数据传输对象
│       ├── entity/        # 实体类
│       └── config/        # 配置类
├── python-ai-service/     # Python AI服务
│   ├── app/
│   │   ├── agent.py       # LangChain Agent实现
│   │   ├── mcp_tools.py   # MCP协议工具
│   │   ├── tools.py       # 核心工具实现
│   │   ├── knowledge_base.py  # 法规知识库
│   │   ├── documents.py   # 文档解析
│   │   └── vector_store.py
│   ├── main.py            # FastAPI主程序
│   └── requirements.txt
├── frontend/              # Vue前端
│   ├── src/
│   │   ├── components/    # 页面组件
│   │   ├── App.vue
│   │   └── main.js
│   └── package.json
└── docs/
    ├── 项目启动指南.md
    ├── 需求文档说明书.md
    ├── 系统设计文档说明书.md
    ├── 团队分工文档.md
    └── Git提交示例.md
```

## 快速开始

### 前置要求
- Java 17+
- Python 3.9+
- Node.js 18+
- Maven 3.8+

### 启动步骤

**1. 启动Python AI服务**
```bash
cd python-ai-service
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
python main.py
```
访问 http://localhost:8000/docs

**2. 启动Java后端**
```bash
cd java-backend
mvn spring-boot:run
```
访问 http://localhost:8080

**3. 启动前端**
```bash
cd frontend
npm install
npm run dev
```
访问 http://localhost:3000

## API接口

### Java后端
- `POST /api/applications` - 创建取水申请
- `GET /api/applications` - 获取申请列表
- `GET /api/applications/{id}` - 获取申请详情
- `POST /api/applications/{id}/ai-review` - 触发AI智能审核

### Python AI服务
- `POST /api/review` - 智能审核申请
- `POST /api/check-completeness` - 材料完整性检查
- `GET /api/knowledge/search` - 知识库搜索
- `GET /api/mcp/tools` - 获取MCP工具列表

## 测试示例

### 测试智能审核
```bash
curl -X POST http://localhost:8000/api/review \
  -H "Content-Type: application/json" \
  -d '{
    "application": {
      "applicant_name": "张三",
      "applicant_id": "123456789",
      "project_name": "农田灌溉项目",
      "water_use": "农业用水",
      "location": "某省某市某村",
      "attachments": ["水资源论证报告.pdf"]
    }
  }'
```

## 团队分工

| 成员 | 职责 |
|------|------|
| 成员1 | Java后端开发、API设计 |
| 成员2 | Vue前端开发、界面交互 |
| 成员3 | Python AI服务、LangChain Agent |
| 成员4 | 文档编写、测试、Git管理 |

## 验收要点
✅ Java Spring Boot 正常启动
✅ Python FastAPI + LangChain 集成
✅ MCP 工具（knowledge_search, check_completeness）
✅ ChromaDB 向量数据库
✅ 前端三个完整页面
✅ 文件上传功能（PDF/Word/TXT）
✅ CORS 跨域配置
✅ Git 仓库与团队分工文档

## 相关文档
- [项目启动指南](项目启动指南.md)
- [需求文档说明书](需求文档说明书.md)
- [系统设计文档说明书](系统设计文档说明书.md)
- [团队分工文档](团队分工文档.md)
- [Git提交示例](Git提交示例.md)

## 最近变更与待办
- 2026-06-01: 已恢复代码到上一次提交，前端 `npm run build` 成功，Python 语法检查通过。
- 待办（优先级高）: 放宽提交附件限制（允许任意上传，不强制全部上传）；更新完整性检测规则：要求至少包含“取水许可申请书”；根据申请类型 (个人/企业) 要求分别提交 `身份证` 或 `营业执照`。

如果想让我直接实现上述变更，我可以先在新分支上完成并运行端到端测试，再发起合并请求。
