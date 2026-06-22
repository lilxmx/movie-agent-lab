# API 设计

所有接口前缀 `/api/v1`，统一响应：`{ "code": 0, "message": "success", "data": ... }`。

## 鉴权
- `POST /auth/login` 登录，返回 JWT
- `POST /auth/register` 注册
- `GET  /auth/me` 当前用户
- `POST /auth/logout` 登出（前端清除 token）

请求头：`Authorization: Bearer <token>`

## 电影
- `GET  /movies?page=&page_size=&q=&type=` 列表 / 搜索（type=0 名称，1 类型）
- `GET  /movies/{id}` 详情
- `GET  /movies/{id}/cast` 演员
- `POST /movies/{id}/rating` 评分
- `GET  /movies/{id}/my-rating` 我的评分
- `POST /movies/{id}/collect` 收藏切换
- `GET  /movies/{id}/is-collected` 是否已收藏
- `GET/POST /movies/{id}/comments` 评论
- `POST /comments/{id}/like` 点赞切换
- `GET  /movies/{id}/quiz` 问答门槛题目
- `GET  /movies/{id}/rating-qualified` 是否有评分资格

## 推荐（统一格式）
- `POST /recommendations/classic` 传统推荐（scene: hot/similar/personalized）
- `POST /recommendations/agent` Agent 推荐

## 对话推荐
- `POST /chat/sessions` 新建会话
- `GET  /chat/sessions/{id}/messages` 历史
- `POST /chat/sessions/{id}/messages` 发送消息，返回回复 + 推荐卡片

## 其他
- `GET  /memory/profile/{user_id}` 用户画像
- `POST /knowledge/index` / `POST /knowledge/search` 知识库
- `GET  /eval/metrics/coverage` 覆盖率
- `GET  /config/client` 前端运行时配置（CDN、推荐模式）
