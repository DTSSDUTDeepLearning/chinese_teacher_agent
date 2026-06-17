# 实施任务清单：初中语文教师智能体

## Phase 1：项目骨架搭建

### 1.1 后端初始化
- [ ] 创建 Python 虚拟环境，安装依赖：`fastapi`, `uvicorn`, `pydantic`, `python-dotenv`, `pydantic-settings`, `openai`, `redis`, `aiomysql` / `sqlalchemy`
- [ ] 创建 `main.py`，配置 FastAPI 应用入口，添加 CORS 中间件
- [ ] 创建 `.env.example`，定义 `DEEPSEEK_API_KEY`, `DATABASE_URL`, `REDIS_URL`
- [ ] 创建 `config.py`（pydantic-settings），统一管理环境变量与配置
- [ ] 创建 `database.py`，配置 SQLAlchemy 异步引擎与会话管理
- [ ] 创建 `models.py`，定义 `Conversation` 等数据模型
- [ ] 创建 `llm_client.py`，封装 DeepSeek API 调用（统一异常处理与重试）

### 1.2 前端初始化
- [ ] 使用 Vite 创建 Vue 3 项目：`npm create vite@latest frontend -- --template vue`
- [ ] 安装依赖：`ant-design-vue`, `echarts`, `vue-echarts`, `marked`, `clipboard`
- [ ] 配置 Vite 代理：`/api` → `http://localhost:8000`
- [ ] 创建基础布局：`App.vue`（顶部导航 + 左侧菜单 + 主内容区路由出口）
- [ ] 配置 Vue Router，定义路由：`/`, `/quiz`, `/knowledge`, `/essay`
- [ ] 创建通用组件：`ChatInput.vue`, `CopyButton.vue`, `MarkdownRenderer.vue`

### 1.3 数据库与缓存
- [ ] 编写 Alembic 迁移脚本（或手动 SQL），创建 `conversations` 表
- [ ] 配置 Redis 连接，封装会话读写方法
- [ ] 验证后端 → MySQL → Redis 全链路连通

---

## Phase 2：功能1 — 古诗文默写出题

### 2.1 后端实现
- [ ] 创建 `routers/quiz.py`，定义 `POST /api/v1/quiz/generate`
- [ ] 创建 `services/quiz_service.py`，实现 Prompt 组装与 LLM 调用
- [ ] 定义 Pydantic 模型：`QuizGenerateRequest`, `QuizQuestion`, `QuizGenerateResponse`
- [ ] 实现 LLM 输出 JSON 解析与校验，容错处理格式异常
- [ ] 添加单元测试（手动 Postman 验证即可）：正常生成、边界条件、格式错误

### 2.2 前端实现
- [ ] 创建 `views/QuizView.vue`
- [ ] 实现筛选表单：年级(七/八/九/全)、学期(上/下/全部)、体裁(诗词/文章/全部)、重要性(全部/仅重点)
- [ ] 实现题目展示区与答案区，用 `a-tabs` 或上下分栏展示
- [ ] 实现一键复制功能（题目、答案分别复制）
- [ ] 对接后端 API，处理加载态与错误态

---

## Phase 3：功能2 — 课文背景与知识图谱

### 3.1 后端实现
- [ ] 创建 `routers/knowledge.py`，定义 `POST /api/v1/knowledge/query` 和 `POST /api/v1/knowledge/graph`
- [ ] 创建 `services/knowledge_service.py`
  - [ ] 实现指令解析：识别"作者生平""创作背景""文学流派""知识图谱"
  - [ ] 实现文字内容 Prompt 组装与调用
  - [ ] 实现知识图谱数据 Prompt 组装与调用，输出 `nodes` + `edges` JSON
- [ ] 定义 Pydantic 模型：`KnowledgeQueryRequest`, `KnowledgeGraphRequest`, `GraphNode`, `GraphEdge`

### 3.2 前端实现
- [ ] 创建 `views/KnowledgeView.vue`
- [ ] 实现指令输入框与发送按钮
- [ ] 实现文字内容展示区（MarkdownRenderer）
- [ ] 集成 ECharts Graph，实现力导向图渲染
- [ ] 实现图谱交互：拖拽节点、缩放、全屏展示
- [ ] 对接后端 API，处理加载态与错误态

---

## Phase 4：功能3 — 命题作文出题

### 4.1 后端实现
- [ ] 创建 `routers/essay.py`，定义会话管理接口
  - [ ] `POST /api/v1/essay/start` — 创建会话，生成初稿
  - [ ] `POST /api/v1/essay/iterate` — 多轮迭代
  - [ ] `POST /api/v1/essay/finalize` — 确认最终版本
- [ ] 创建 `services/essay_service.py`
  - [ ] 实现会话创建与 Redis/MySQL 存储
  - [ ] 实现 Prompt 组装（含当前配置与历史对话）
  - [ ] 实现多轮对话上下文拼接
- [ ] 定义 Pydantic 模型：`EssayStartRequest`, `EssayIterateRequest`, `EssayFinalizeRequest`, `EssaySession`
- [ ] 实现会话过期清理机制（定时任务或惰性清理）

### 4.2 前端实现
- [ ] 创建 `views/EssayView.vue`
- [ ] 实现对话式聊天界面（类似 ChatGPT）
- [ ] 实现配置面板：主题、类型(中考/普通)、文体、字数、难度、附加要求
- [ ] 实现"开始出题" → 展示初稿 → 输入修改意见 → 展示优化稿 的完整交互
- [ ] 实现"确认最终版本"按钮，展示最终题目
- [ ] 对接后端 API，处理会话状态管理与错误态

---

## Phase 5：联调优化与部署准备

### 5.1 联调测试
- [ ] 三个功能端到端测试，验证完整链路
- [ ] 测试错误场景：LLM 超时、格式异常、网络断开
- [ ] 测试多轮对话会话的上下文连续性
- [ ] 收集输出样例，验证 Prompt 效果，必要时调优

### 5.2 界面优化
- [ ] 统一整体视觉风格（Ant Design Vue 主题定制）
- [ ] 移动端适配（响应式布局检查）
- [ ] 添加加载动画、空状态、错误提示等体验细节

### 5.3 文档与部署
- [ ] 编写 `docs/deployment.md`，记录本地启动步骤
- [ ] 确保 `.env` 不提交 Git，`.env.example` 包含所有必需变量
- [ ] 验证项目可在干净环境中按文档步骤启动

---

## 验收标准

- [ ] 功能1：教师配置筛选条件后，能生成准确的古诗文填空题，题目与答案分开展示，支持复制。
- [ ] 功能2：教师输入指令后，能输出课文背景文字内容和可视化知识图谱，图谱支持交互。
- [ ] 功能3：教师能通过多轮对话协商生成满意的作文题目，会话上下文连续不丢失。
- [ ] 所有功能均通过后端代理调用 DeepSeek API，前端不暴露 API Key。
- [ ] 项目可在本地一键启动（`uvicorn` + `npm run dev`），有清晰的启动文档。
