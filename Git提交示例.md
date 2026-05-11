# Git提交示例与说明

## Git仓库初始化
```bash
cd water-approval-system
git init
```

## 配置不同用户提交（示例）

### 提交1：张三初始化Java后端
```bash
# 配置张三的用户信息
git config user.name "张三"
git config user.email "zhangsan@example.com"

# 添加Java后端文件
git add java-backend/pom.xml
git add java-backend/src/main/java/com/waterapproval/WaterApprovalApplication.java
git add java-backend/src/main/java/com/waterapproval/config/WebConfig.java
git add java-backend/src/main/java/com/waterapproval/entity/Application.java
git add java-backend/src/main/resources/application.yml

# 提交
git commit -m "feat: 初始化Java Spring Boot后端项目"

git add java-backend/src/main/java/com/waterapproval/controller/ApplicationController.java
git add java-backend/src/main/java/com/waterapproval/service/ApplicationService.java
git add java-backend/src/main/java/com/waterapproval/repository/ApplicationRepository.java

git commit -m "feat: 实现申请管理API接口"
```

### 提交2：李四初始化前端
```bash
# 配置李四的用户信息
git config user.name "李四"
git config user.email "lisi@example.com"

git add frontend/package.json
git add frontend/vite.config.js
git add frontend/index.html
git add frontend/src/main.js
git add frontend/src/App.vue

git commit -m "feat: 初始化Vue 3前端项目"

git add frontend/src/components/ApplicationList.vue
git add frontend/src/components/CreateApplication.vue
git add frontend/src/components/ReviewResult.vue

git commit -m "feat: 实现申请列表、新建申请、审核结果三个页面"
```

### 提交3：王五初始化Python AI服务
```bash
# 配置王五的用户信息
git config user.name "王五"
git config user.email "wangwu@example.com"

git add python-ai-service/requirements.txt
git add python-ai-service/main.py
git add python-ai-service/app/config.py

git commit -m "feat: 初始化Python FastAPI AI服务"

git add python-ai-service/app/vector_store.py
git add python-ai-service/app/embeddings.py
git add python-ai-service/app/documents.py
git add python-ai-service/app/tools.py
git add python-ai-service/app/service.py

git commit -m "feat: 实现向量存储、文档解析和知识库工具"
```

### 提交4：赵六添加文档
```bash
# 配置赵六的用户信息
git config user.name "赵六"
git config user.email "zhaoliu@example.com"

git add README.md
git add 需求文档说明书.md
git add 系统设计文档说明书.md

git commit -m "docs: 添加项目README、需求文档和设计文档"

git add 团队分工文档.md
git add .gitignore

git commit -m "docs: 添加团队分工文档和.gitignore"
```

## 提交规范说明

### 提交信息格式
```
<type>: <subject>

<body>

<footer>
```

### Type类型
- `feat`: 新功能
- `fix`: 修复
- `docs`: 文档
- `style`: 格式调整
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

### Subject规范
- 使用现在时动词
- 首字母小写
- 结尾不用句号

## 分支策略
```
main                # 主分支
├── feature/java    # Java后端功能分支
├── feature/frontend # 前端功能分支  
└── feature/ai      # AI服务功能分支
```

## 远程仓库（可选）
```bash
# 添加远程仓库
git remote add origin <仓库地址>

# 推送分支
git push -u origin main
```
