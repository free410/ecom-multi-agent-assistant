# 多 Agent 电商运营智能助手平台

<p align="center">
  <img src="./docs/assets/hero.svg" alt="多 Agent 电商运营智能助手平台封面" width="100%" />
</p>

<p align="center">
  <a href="https://github.com/free410/ecom-multi-agent-assistant/actions/workflows/ci.yml">
    <img src="https://img.shields.io/github/actions/workflow/status/free410/ecom-multi-agent-assistant/ci.yml?branch=main&label=CI&style=for-the-badge" alt="CI" />
  </a>
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11" />
  <img src="https://img.shields.io/badge/FastAPI-LangGraph-111827?style=for-the-badge&logo=fastapi&logoColor=00C7B7" alt="FastAPI LangGraph" />
  <img src="https://img.shields.io/badge/React-Vite-111827?style=for-the-badge&logo=react&logoColor=61DAFB" alt="React Vite" />
  <img src="https://img.shields.io/badge/License-MIT-16A34A?style=for-the-badge" alt="MIT License" />
</p>

<p align="center">
  一个面向电商运营场景的多 Agent AI 应用 MVP，支持商品问答、活动文案、客服辅助、评论分析、竞品整理与运营日报生成。
</p>

## 项目亮点

- 基于 `LangGraph` 实现多 Agent 有状态工作流，完整覆盖 `意图识别 -> 路由 -> Tool Calling -> 汇总输出`
- 支持 `Qwen / DeepSeek / Mock` 三种模型接入方式，未配置时自动回退 `Mock`
- 后端采用 `FastAPI + SQLAlchemy + Redis + MySQL`，支持降级运行
- 前端采用 `React + Vite + TypeScript`，内置结构化结果区、执行面板与工具工作流看板
- 内置完整 `seed mock data`，无需真实电商 API 即可本地演示
- 支持 `session_id`、短期记忆、偏好记忆、工具耗时和执行链路展示

## 页面预览

### 运行界面

<p align="center">
  <img src="./docs/assets/app-showcase.svg" alt="应用运行界面预览" width="100%" />
</p>

### 多 Agent 工作流

<p align="center">
  <img src="./docs/assets/workflow.svg" alt="多 Agent 工作流示意" width="100%" />
</p>

### 工具与数据层

<p align="center">
  <img src="./docs/assets/tooling-overview.svg" alt="工具与数据层示意" width="100%" />
</p>

## 主要功能

| 模块 | 能力说明 |
| --- | --- |
| 商品问答 | 根据商品卖点、适用人群、FAQ 与售后规则回答商品问题 |
| 活动文案生成 | 根据商品卖点、活动主题和目标人群生成促销文案 |
| 客服辅助回复 | 根据用户问题、FAQ 与售后规则生成客服建议回复 |
| 评论摘要 | 汇总近期评论、提取差评关键词并输出运营建议 |
| 竞品整理 | 对竞品亮点、价格带、短板进行结构化整理和对比 |
| 运营日报 | 根据任务执行结果与输入上下文自动生成日报 |
| 执行可视化 | 展示 `intent / confidence / routing_reason / agent_path / used_tools / logs` |

## 系统架构

### Agent 角色

1. `IntentAgent`
   负责意图识别、字段提取、上下文恢复与补充信息判断。
2. `ProductKnowledgeAgent`
   负责商品知识检索、FAQ 匹配与商品问答。
3. `ContentAgent`
   负责活动文案、卖点表达与营销内容生成。
4. `SupportAgent`
   负责客服回复建议与售后安抚话术生成。
5. `AnalysisAgent`
   负责评论摘要、竞品整理与日报分析。
6. `SummaryAgent`
   负责统一汇总最终输出，适配前端展示结构。

### Tool Calling

- `get_product_info(product_name)`
- `search_product_faq(product_name, question)`
- `summarize_reviews(product_name, days=7)`
- `extract_negative_keywords(product_name, days=7)`
- `generate_campaign_copy(product_name, campaign_theme, audience)`
- `build_customer_reply(product_name, user_question)`
- `compare_competitors(product_name)`
- `generate_daily_report(input_context)`

## 技术栈

### 后端

- Python 3.11
- FastAPI
- LangGraph
- LangChain compatibility layer
- SQLAlchemy
- Pydantic
- Redis
- MySQL
- Uvicorn

### 前端

- React
- Vite
- TypeScript
- Axios
- React Markdown
- CSS

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

返回服务健康状态、数据库状态、Redis 状态和模型提供方状态。

### `POST /api/chat`

请求示例：

```json
{
  "session_id": "demo-session-001",
  "message": "根据逐光护眼台灯的卖点生成一版宿舍党促销文案",
  "model_provider": "mock"
}
```

响应核心字段：

```json
{
  "session_id": "demo-session-001",
  "intent": "campaign_copy",
  "answer": "...",
  "logs": ["..."],
  "used_tools": ["generate_campaign_copy"],
  "agent_path": ["ContextLoader", "IntentAgent", "ContentAgent", "SummaryAgent"],
  "provider_used": "mock",
  "structured_result": {},
  "confidence": 0.88,
  "routing_reason": "命中文案关键词",
  "memory_used": {
    "short_term_memory": true,
    "preference_memory": false
  }
}
```

### 其他接口

- `GET /api/session/{session_id}`：获取指定会话详情与最近一次执行结果
- `GET /api/sessions`：获取历史会话列表
- `DELETE /api/session/{session_id}`：删除指定会话
- `GET /api/products`：获取内置商品列表
- `POST /api/seed/init`：初始化商品、评论和竞品 mock 数据

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
MYSQL_URL=mysql+pymysql://your_mysql_user:your_mysql_password@127.0.0.1:3306/ecom_agent
REDIS_URL=redis://localhost:6379/0
QWEN_API_KEY=your_qwen_api_key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
DEFAULT_PROVIDER=mock
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

注意：

- `.env`、`frontend/.env.local` 等本地环境文件不会提交到 Git
- 提交前请只保留 `.env.example` 这类模板文件，不要把真实 API Key 或数据库密码写进仓库

### 3. 启动依赖服务

如果本机没有单独启动 MySQL / Redis：

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

- API Docs：`http://localhost:8000/docs`
- Health Check：`http://localhost:8000/api/health`

### 5. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端地址：

- App：`http://localhost:5173`

首次打开页面时，前端会自动调用 `/api/seed/init` 初始化演示数据。

## 演示示例

你可以直接在页面里输入这些问题：

- `逐光护眼台灯适合宿舍党吗？它的核心卖点和常见问题有哪些？`
- `根据森语香薰加湿器的卖点，生成一版面向租房女生的开学季促销文案`
- `针对清汐电热饭盒用户反馈“加热速度慢，午休时间不够用”，生成客服回复建议`
- `总结轻氧便携榨汁杯最近7天差评关键词，并归纳主要问题`
- `整理逐光护眼台灯与竞品的差异，给我一个运营角度的对比结论`
- `结合今天的活动文案调整、客服问题和评论分析，生成一版简洁运营日报`
- `给我写一个文案`
- `耳机`

## 数据与降级策略

### 内置数据

- 商品：12 条
- 评论：60+ 条
- 竞品：8 条
- 数据位置：`backend/app/seed/`

### 降级行为

- MySQL 不可用：自动回退到内存存储
- Redis 不可用：自动回退到内存缓存
- 模型 Key 不可用：自动回退到 `mock`
- 远程模型超时：自动 fallback 到 `mock`

## 测试与 CI

### 本地测试

后端：

```bash
cd backend
pytest -q
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

## 简历展示建议

- 适合作为“AI 应用开发实习生 / 全栈 AI 项目”展示项目
- 亮点在于多 Agent 工作流、Tool Calling、结构化输出、记忆恢复与前端可视化联动
- 同时兼顾工程落地与可演示性，适合讲解“从模型调用到业务工作流编排”的完整链路

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
