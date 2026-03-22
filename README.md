# 多 Agent 电商运营智能助手平台

<p align="center">
  <img src="./docs/assets/hero.svg" alt="project hero" width="100%" />
</p>

<p align="center">
  <a href="https://github.com/free410/ecom-multi-agent-assistant/actions/workflows/ci.yml">
    <img src="https://img.shields.io/github/actions/workflow/status/free410/ecom-multi-agent-assistant/ci.yml?branch=main&label=CI&style=for-the-badge" alt="ci badge" />
  </a>
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="python" />
  <img src="https://img.shields.io/badge/FastAPI-LangGraph-111827?style=for-the-badge&logo=fastapi&logoColor=00C7B7" alt="fastapi langgraph" />
  <img src="https://img.shields.io/badge/React-Vite-111827?style=for-the-badge&logo=react&logoColor=61DAFB" alt="react vite" />
  <img src="https://img.shields.io/badge/License-MIT-16A34A?style=for-the-badge" alt="mit license" />
</p>

<p align="center">
  面向电商运营场景的多 Agent AI 应用 MVP，支持商品问答、活动文案生成、客服辅助回复、评论摘要、竞品整理与运营日报生成。
</p>

## 项目亮点

- 基于 `LangGraph` 的有状态多 Agent 工作流，完整体现 `意图识别 -> 路由 -> 工具调用 -> 汇总输出`
- 支持 `Qwen / DeepSeek / Mock` 三种 provider 路由，缺少 Key 时自动回退 mock 模式
- 使用 `Redis` 存会话记忆与最近执行结果，`MySQL` 存商品、会话与任务日志
- 后端使用 `FastAPI`，前端使用 `React + Vite + TypeScript`
- 内置 `seed mock data`，无需真实电商 API 也能本地完整演示
- 支持降级运行：MySQL / Redis 不可用时自动切换到内存模式
- 仓库已配置 `GitHub Actions CI`，自动跑后端测试与前端构建

## 仓库预览

### Running UI Screenshot

> 下面这张图来自项目本地运行后的真实页面截图，展示了模型切换、会话列表、Markdown 回答和执行链路面板。

<p align="center">
  <img src="./docs/assets/app-screenshot.png" alt="running app screenshot" width="100%" />
</p>

### UI Layout Illustration

<p align="center">
  <img src="./docs/assets/ui-preview.svg" alt="ui layout illustration" width="100%" />
</p>

### Workflow Overview

<p align="center">
  <img src="./docs/assets/workflow.svg" alt="workflow" width="100%" />
</p>

## 功能清单

| 模块 | 能力 |
| --- | --- |
| 商品问答 | 根据商品卖点、适用人群、FAQ、售后规则组织回答 |
| 活动文案生成 | 根据商品卖点、活动主题、人群定向生成促销文案 |
| 客服辅助回复 | 对售后、物流、FAQ 类问题生成客服建议回复 |
| 评论摘要 | 提取评论关键词、汇总情绪、总结问题 |
| 竞品整理 | 对竞品卖点、价格带、弱点做结构化对比 |
| 运营日报 | 根据任务执行结果和输入上下文输出日报 |
| 执行可视化 | 返回 `intent / agent_path / used_tools / logs` 供前端展示 |

## 技术栈

### Backend

- Python 3.11
- FastAPI
- LangGraph
- LangChain compatibility layer
- SQLAlchemy
- Pydantic
- Redis
- MySQL
- Uvicorn

### Frontend

- React
- Vite
- TypeScript
- Axios
- React Markdown
- CSS

## 系统架构

### Agent 角色

1. `IntentAgent`
   识别意图，提取商品名、活动主题、目标人群等上下文
2. `ProductKnowledgeAgent`
   处理商品问答和商品知识检索
3. `ContentAgent`
   处理活动文案和营销内容生成
4. `SupportAgent`
   处理客服回复建议
5. `AnalysisAgent`
   处理评论摘要、竞品整理、日报生成
6. `SummaryAgent`
   统一整理最终结构化输出

### Tool Calling

- `get_product_info(product_name)`
- `search_product_faq(product_name, question)`
- `summarize_reviews(product_name, days=7)`
- `extract_negative_keywords(product_name, days=7)`
- `generate_campaign_copy(product_name, campaign_theme, audience)`
- `build_customer_reply(product_name, user_question)`
- `compare_competitors(product_name)`
- `generate_daily_report(input_context)`

## 目录结构

```text
ecom-multi-agent-assistant/
  backend/
    app/
      api/
      agents/
      core/
      graph/
      models/
      schemas/
      seed/
      services/
      tools/
      main.py
    tests/
    requirements.txt
  frontend/
    src/
      api/
      components/
      hooks/
      pages/
      types/
      App.tsx
      main.tsx
    package.json
  docs/
    assets/
  .github/
    workflows/
  docker-compose.yml
  .env.example
  LICENSE
  README.md
```

## API 设计

### `GET /api/health`

返回服务健康状态、MySQL 状态和 Redis 状态。

### `POST /api/chat`

请求示例：

```json
{
  "session_id": "demo-session-001",
  "message": "根据云萃保温咖啡杯的卖点生成618促销文案",
  "model_provider": "mock"
}
```

响应示例：

```json
{
  "session_id": "demo-session-001",
  "intent": "campaign_copy",
  "answer": "...",
  "logs": ["..."],
  "used_tools": ["generate_campaign_copy"],
  "agent_path": ["ContextLoader", "IntentAgent", "ContentAgent", "SummaryAgent"],
  "provider_used": "mock"
}
```

### `GET /api/session/{session_id}`

返回会话历史和最近一次执行结果。

### `GET /api/sessions`

返回历史会话列表。

### `GET /api/products`

返回内置 mock 商品列表。

### `POST /api/seed/init`

初始化 mock 商品、评论和竞品数据。

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/free410/ecom-multi-agent-assistant.git
cd ecom-multi-agent-assistant
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，按需填写：

```env
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_PORT=5173
MYSQL_URL=mysql+pymysql://root:123456@localhost:3306/ecom_agent
REDIS_URL=redis://localhost:6379/0
QWEN_API_KEY=
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
DEFAULT_PROVIDER=mock
VITE_API_BASE_URL=http://localhost:8000/api
```

### 3. 启动可选依赖服务

如果本地没有 MySQL / Redis：

```bash
docker compose up -d
```

### 4. 启动后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端地址：

- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/health`

### 5. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端地址：

- App: `http://localhost:5173`
- Demo Entry: `http://localhost:5173`

首次打开页面时，前端会自动调用 `/api/seed/init` 初始化演示数据。

## 演示问题

你可以直接在页面中点击这些预置问题：

- `根据云萃保温咖啡杯的卖点生成618促销文案`
- `总结云萃保温咖啡杯最近7天差评关键词`
- `针对云萃保温咖啡杯用户反馈“发货慢”生成客服回复建议`
- `整理云萃保温咖啡杯与竞品的差异`
- `生成今天的运营日报`

## 数据与降级策略

### 内置数据

- 商品：6 条
- 评论：24 条
- 竞品：4 条
- 数据位置：`backend/app/seed/`

### 降级行为

- MySQL 不可用：自动切到内存存储
- Redis 不可用：自动切到内存缓存
- 模型 Key 不可用：自动切到 `mock_llm`
- 远程模型失败：自动 fallback 到 mock 模式

## 测试与 CI

### 本地测试

后端：

```bash
cd backend
pytest
```

前端构建：

```bash
cd frontend
npm run build
```

### GitHub Actions

仓库已配置 `.github/workflows/ci.yml`：

- `backend` job：安装依赖并运行 `pytest`
- `frontend` job：安装依赖并执行 `npm run build`

## 适合简历展示的点

- 多 Agent 架构与状态图清晰，适合讲解 AI 应用链路设计
- 具备 Tool Calling、会话记忆、缓存、结构化日志与前端可视化
- 兼顾工程性和演示性，支持没有业务 API 时的完整本地 Demo
- 前后端分离，具备基础测试和 CI，适合作为 AI 应用开发实习作品

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
