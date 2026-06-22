# Movie Agent Lab

AI-native 电影 Agent 推荐实验平台。由旧项目 `integrated-rec-sys`（Spring Boot + Vue2）
重构而来，聚焦对话推荐、Agent Memory、知识库、传统推荐模型、Agent 推荐与评测沙箱。

## 技术栈
- 前端：Vue3 + Vite + TypeScript + Pinia
- 后端：FastAPI + Pydantic + SQLAlchemy + Alembic
- 存储：MySQL（复用旧库）+ Redis + 向量库抽象层
- 部署：Docker Compose

## 三条主线
- 传统推荐：热门、相似、Embedding、NeuralCF、Wide&Deep
- Agent 推荐：基于意图、Memory、知识库的独立路线
- Chatbot 对话推荐：自然语言观影需求入口

## 快速开始

### 后端
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # 按需修改数据库 / Redis / LLM 配置
uvicorn app.main:app --reload
# 创建 AI-native 新表
alembic upgrade head
```

### 前端
```bash
cd frontend
npm install
cp .env.example .env   # 配置 VITE_API_BASE_URL
npm run dev
```

### 一键容器编排
```bash
cd infra
docker compose up --build
```

## 目录
- `backend/` FastAPI 后端（分层架构，推荐策略可插拔）
- `frontend/` Vue3 前端（ChatRecommend 为核心页面）
- `infra/` Docker Compose 与中间件配置
- `docs/` 架构、API、迁移文档
