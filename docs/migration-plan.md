# 迁移计划

旧项目（Spring Boot + Vue2）仅作业务逻辑与数据结构参考，不机械翻译。

| Phase | 内容 | 状态 |
|---|---|---|
| 1 | FastAPI + Vue3 + Docker 骨架 | 完成 |
| 2 | 映射旧 MySQL（user/movie/rating/collect 等）+ JWT 鉴权 | 完成 |
| 3 | 电影列表/详情/评分/收藏/演员/评论/问答门槛 | 完成 |
| 4 | classic pipeline（Embedding 相似、个性化、ABTest、TF Serving） | 完成 |
| 5 | Agent 推荐 mock pipeline + 前端切换 | 完成 |
| 6 | ChatRecommend 三栏页面 + chatbot + LLM Provider 抽象 | 完成 |
| 7 | Alembic 新表（recommendation_runs/chat_*/agent_memories） | 完成 |
| 8 | 向量库抽象层（knowledge collection） | 完成 |
| 9 | 真实 RAG / Agent Memory / 评测沙箱 | 预留扩展点 |

## 关键注意事项
1. 旧库密码为 `MD5(password + salt)`，登录沿用该规则兼容存量用户。
2. `movie_genres` 与 `user_like_genres` 为竖线分隔字符串，不改格式。
3. 相似电影向量优先 `itemEmb`，回退 `graphEmb`。
4. ABTest 改用 `int(user_id) % 3` 分桶（Java hashCode 无法在 Python 复现）。
5. TF Serving 通过 `TF_SERVING_ENABLED` 开关，关闭时回退按平均分排序。
6. 所有公网 IP / 模型地址 / API Key / 图片路径均配置化（见 `.env.example`）。

## 旧库导入
将旧 MySQL 的 SQL 文件放入 `infra/mysql/init/`，`docker compose up` 首次启动自动导入。
新表执行 `alembic upgrade head` 创建。
