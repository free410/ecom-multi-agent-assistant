# 多 Agent 电商运营智能助手平台

一个面向电商运营场景的多 Agent AI 应用 MVP，支持商品问答、活动文案生成、客服辅助回复、评论摘要、竞品整理和运营日报生成。项目采用前后端分离 monorepo 结构，后端使用 FastAPI + LangGraph，前端使用 React + Vite，并内置 mock 数据和 mock LLM 降级模式，保证没有真实电商 API、没有 Redis/MySQL、没有模型 Key 时也能跑通演示。

## 技术栈

### 后端
- Python 3.11
- FastAPI
- LangGraph
- SQLAlchemy
- Pydantic
- Redis
- MySQL
- Uvicorn
- httpx

### 前端
- React
- Vite
- TypeScript
- Axios
- React Markdown
- 基础 CSS

## 核心功能

- 商品问答：根据商品卖点、适用人群、FAQ 和售后规则回答问题
- 活动文案生成：根据活动主题和目标人群生成营销文案
- 客服辅助回复：基于商品信息和售后规则生成回复建议
- 评论摘要：总结最近评论、提取差评关键词、归纳问题
- 竞品整理：对竞品信息进行结构化对比
- 运营日报：根据输入上下文生成日报
- 多 Agent 路由：IntentAgent -> 对应业务 Agent -> SummaryAgent
- Tool Calling：所有业务先走工具层，再组织回答
- Redis 记忆：保存会话历史和最近一次执行结果
- MySQL 存储：保存商品、会话、任务日志
- Provider 切换：支持 Qwen / DeepSeek / Mock
- 降级运行：MySQL/Redis/真实模型不可用时自动切到内存或 mock 模式

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
      styles.css
    package.json
  .env.example
  docker-compose.yml
  README.md
```

## 多 Agent 工作流

系统基于 LangGraph 状态工作流运行，主链路如下：

1. `ContextLoader`
   读取 Redis 或内存中的会话历史
2. `IntentAgent`
   识别用户意图，提取商品名、活动主题、人群等上下文
3. 路由到对应 Agent
   - `ProductKnowledgeAgent`
   - `ContentAgent`
   - `SupportAgent`
   - `AnalysisAgent`
4. 工具调用
   先调用商品、评论、竞品、日报等工具函数，获得结构化结果
5. `SummaryAgent`
   汇总 intent、agent_path、used_tools、logs 和最终回答

## API 设计

### `GET /api/health`
返回服务健康状态、数据库状态和 Redis 状态。

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
返回内置商品列表。

### `POST /api/seed/init`
初始化商品、评论、竞品 mock 数据。

## 环境变量

根目录创建 `.env`，可参考 `.env.example`：

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

### Provider 切换规则

- 显式选择 `mock` 时，直接使用 mock 模式
- 选择 `qwen` 或 `deepseek` 但缺少 `api_key` / `base_url` 时，自动回退 `mock`
- 远程模型调用失败时，也会自动回退 `mock`

## 启动方式

### 1. 启动可选依赖服务

如果本地没有 MySQL / Redis，先执行：

```bash
docker compose up -d
```

### 2. 启动后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端启动后：
- 文档地址：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/api/health`

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端地址：

```text
http://localhost:5173
```

首次打开页面时，前端会自动请求 `/api/seed/init` 初始化 mock 数据。

## 主要演示问题

可以直接在前端点击这些示例：

- 根据云萃保温咖啡杯的卖点生成618促销文案
- 总结云萃保温咖啡杯最近7天差评关键词
- 针对云萃保温咖啡杯用户反馈“发货慢”生成客服回复建议
- 整理云萃保温咖啡杯与竞品的差异
- 生成今天的运营日报

## 数据与降级策略

### 数据源

- 商品：6 条
- 评论：24 条
- 竞品：4 条
- 文件位置：`backend/app/seed/`

### 降级行为

- MySQL 不可用：自动切到内存存储
- Redis 不可用：自动切到内存缓存
- 模型 Key 不可用：自动切到 mock LLM

## 测试

后端包含 5 条以上接口测试，运行方式：

```bash
cd backend
pytest
```

测试覆盖：

- 健康检查
- seed 初始化
- 商品列表
- 文案生成路由
- 评论分析路由
- 会话详情查询

## 简历项目亮点

- 使用 LangGraph 设计有状态多 Agent 工作流
- 体现 Tool Calling、会话记忆、缓存和降级运行设计
- 支持 OpenAI 兼容接口切换 Qwen / DeepSeek
- 前端可视化展示 intent、agent_path、used_tools 和 logs
- 不依赖真实业务 API，也能完整演示 AI 电商运营场景

