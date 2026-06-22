# 架构说明

Movie Agent Lab 是 AI-native 电影 Agent 推荐实验平台，包含三条独立主线：传统推荐、Agent 推荐、Chatbot 对话推荐。

## 分层架构（后端）

```
api/v1/        路由层，仅做参数校验与响应包装
services/      业务编排
repositories/  数据访问（SQLAlchemy）
models/        ORM 模型（旧表只读映射 + AI-native 新表）
recsys/        推荐内核（contracts/registry/classic/agentic/metrics）
chatbot/       对话推荐
memory/        浏览历史与用户画像
knowledge/     知识库与向量库抽象
core/          配置、数据库、Redis、安全、LLM Provider、依赖
```

## 推荐策略可插拔

`recsys/contracts.py` 定义统一接口 `Recommender` 与返回格式 `RecResult`，
`recsys/registry.py` 按 mode 注册策略。传统推荐与 Agent 推荐返回同一格式，
前端按钮切换 `[传统推荐] [Agent 推荐]` 调用不同接口即可。

## 数据层策略

第一阶段复用旧 MySQL，ORM 仅映射不修改旧表；AI-native 新表由 Alembic 单独管理
（见 `alembic/env.py` 的 `_MANAGED_TABLES` 白名单）。旧 Redis 中的 embedding
（itemEmb / graphEmb / userEmb）继续用于传统推荐。
