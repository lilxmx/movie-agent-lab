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

---

## 生产环境部署（云服务器）

本节记录把项目部署到 Linux 云服务器的完整步骤，**复用服务器宿主机已有的 MySQL / Redis**，只用 Docker 起前端和后端两个容器。适用场景：服务器已经装好 MySQL/Redis（例如复用旧项目 `integrated-rec-sys` 的数据库）。

### 部署架构

```
┌─────────── 云服务器（如 43.138.158.143） ───────────┐
│                                                     │
│  宿主机直接安装的服务                                │
│  ├── MySQL    :3306   ← 旧项目数据（电影、评分等）   │
│  ├── Redis    :6379                                  │
│  ├── Nginx    :80                                    │
│  └── TF Serving :8501/8502/8503（可选）              │
│              ↑                                        │
│              │ host.docker.internal（容器→宿主机）    │
│              │                                        │
│  Docker 容器                                          │
│  ├── infra-backend-1  :8000  FastAPI                  │
│  └── infra-frontend-1 :5173  Vue3 + Nginx            │
└─────────────────────────────────────────────────────┘

用户浏览器 → http://服务器IP:5173 → 前端 Nginx
         → http://服务器IP:8000 → 后端 API
```

### 前置条件

- Ubuntu / Debian 服务器（其他发行版类似）
- 已安装 Docker + Docker Compose
- 服务器上已有可用的 MySQL（含旧业务数据）和 Redis
- 已知 MySQL root 密码、Redis 密码
- 拥有项目的 GitHub 私有仓库访问权限（用于 clone）

---

### 第一步：服务器准备

**1.1 把当前用户加入 docker 组（避免每次 sudo）**

```bash
sudo usermod -aG docker $USER
exit   # 必须退出 SSH 重新登录才生效
```

> **说明**：未加入 docker 组时执行 `docker ps` 会报 `permission denied while trying to connect to the Docker daemon socket`。

**1.2 允许 MySQL root 从 Docker 网络访问**

后端容器通过 `host.docker.internal` 连宿主机 MySQL，源 IP 是 docker bridge 网段（一般 `172.17.0.x`），默认 `root@localhost` 拒绝。

```bash
# 检查当前 root 用户允许的 host
sudo mysql -uroot -p<MySQL密码> -e "SELECT user, host FROM mysql.user WHERE user='root';"
```

如果只有 `root | localhost`，加一条远程权限：

```bash
sudo mysql -uroot -p<MySQL密码> <<'EOF'
CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED BY '<MySQL密码>';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;
EOF
```

> **⚠️ 安全提醒**：`root@%` 允许任意 IP 连接，必须在云厂商安全组里**禁止** 3306/6379 端口对公网开放，否则数据库密码暴露在外网。

**1.3 验证 Redis 密码**

```bash
redis-cli -a <Redis密码> ping
# 返回 PONG 即正常
```

---

### 第二步：从 GitHub 拉取代码

**2.1 生成 GitHub Personal Access Token（私有仓库）**

1. 打开 https://github.com/settings/tokens
2. **Generate new token → Generate new token (classic)**
3. 勾选 `repo` 权限，生成并复制 token（形如 `ghp_xxxxxxxx`，只显示一次）

**2.2 在服务器上 clone**

```bash
cd /home/ubuntu
git clone https://github.com/<your-username>/movie-agent-lab.git
# Username: <GitHub 用户名>
# Password: <粘贴 token，不显示任何字符是正常的>
```

> **说明**：仓库的 `.gitignore` 已排除 `backend/.env` 和 `frontend/.env`，所以拉下来不会有生产配置文件，需要手动创建。

---

### 第三步：准备生产配置文件

**在本地 Mac 准备好两个 `.env` 文件**（项目根目录已经有 `.env.prod` 模板可参考）。

**3.1 `backend/.env` 必填项**

```env
APP_NAME="Movie Agent Lab"
APP_ENV=prod
API_V1_PREFIX=/api/v1

# 关键 1：CORS 必须包含浏览器访问的前端地址
CORS_ORIGINS=http://<服务器公网IP>:5173,http://localhost:5173,http://127.0.0.1:5173

# 关键 2：数据库和 Redis 必须用 host.docker.internal（不要写公网 IP）
DB_HOST=host.docker.internal
DB_PORT=3306
DB_USER=root
DB_PASSWORD=<MySQL密码>
DB_NAME=integratedrecsys

REDIS_HOST=host.docker.internal
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=<Redis密码>

# 关键 3：JWT 密钥必须改成随机值（不要用默认）
# 生成方式：openssl rand -hex 32
JWT_SECRET_KEY=<64位随机hex字符串>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# TF Serving（无模型时保持 false，不实际调用）
TF_SERVING_NEURALCF_URL=http://host.docker.internal:8503/v1/models/NeuralCF:predict
TF_SERVING_DEEPCROSSING_URL=http://host.docker.internal:8502/v1/models/DeepCrossing:predict
TF_SERVING_WIDEANDDEEP_URL=http://host.docker.internal:8501/v1/models/WideAndDeep:predict
TF_SERVING_ENABLED=false

# LLM Provider（对话推荐核心）
LLM_PROVIDER=volcano
VOLCANO_API_KEY=<火山方舟 API Key>
VOLCANO_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
VOLCANO_MODEL=<Endpoint ID 或 Model ID>

# 静态资源 CDN（浏览器访问，必须写公网 IP/域名）
POSTER_CDN_URL=http://<服务器公网IP>/posters/
POSTER_BG_CDN_URL=http://<服务器公网IP>/poster_background/
CAST_POSTER_CDN_URL=http://<服务器公网IP>/cast_poster/

VECTOR_STORE_PROVIDER=memory
```

**说明每个关键项**：

| 字段 | 说明 |
|---|---|
| `CORS_ORIGINS` | 后端允许的跨域来源。**必须包含**浏览器实际访问前端的 URL，否则浏览器拦截所有 API 请求 |
| `DB_HOST` / `REDIS_HOST` | 容器内访问宿主机服务的特殊地址。Linux 上需要配合 `extra_hosts` 才能生效（见 docker-compose.prod.yml） |
| `JWT_SECRET_KEY` | 签发用户登录令牌的密钥，必须是长随机字符串。生成命令 `openssl rand -hex 32` |
| `POSTER_CDN_URL` 等 | 海报图给浏览器加载用的，**必须是公网可访问地址**（与 DB_HOST 不同） |

**3.2 `frontend/.env`**

```env
VITE_API_BASE_URL=http://<服务器公网IP>:8000/api/v1
```

> **关键说明**：`VITE_*` 变量是 **Vite 构建时静态注入到 JS 文件**的，不是运行时读取。改了 `.env` 必须**重新 build** 前端镜像才能生效。

**3.3 上传到服务器**

在本地 Mac 终端（不在 SSH 里）：

```bash
scp backend/.env.prod ubuntu@<服务器IP>:/home/ubuntu/movie-agent-lab/backend/.env
scp frontend/.env.prod ubuntu@<服务器IP>:/home/ubuntu/movie-agent-lab/frontend/.env
```

> **不要用 nano/vim 直接在服务器编辑长配置**，容易出现换行丢失、内容拼接的问题（曾经出现过 `predict` 后面直接接下一行 key 导致解析错误）。本地写好 scp 上传最稳。

---

### 第四步：准备 docker-compose.prod.yml

项目里默认的 `infra/docker-compose.yml` 会启动整套（MySQL + Redis + 前后端），**会与宿主机端口冲突**。生产环境只起前后端两个容器，需要单独的 `docker-compose.prod.yml`：

```yaml
services:
  backend:
    build:
      context: ../backend
    env_file:
      - ../backend/.env
    extra_hosts:
      - "host.docker.internal:host-gateway"   # Linux 必备：让容器能解析宿主机
    ports:
      - "8000:8000"
    restart: unless-stopped

  frontend:
    build:
      context: ../frontend
    ports:
      - "5173:80"
    depends_on:
      - backend
    restart: unless-stopped
```

**说明关键点**：

- 没有 mysql/redis 服务 → **复用宿主机现有的**，避免端口冲突、保留旧数据
- `extra_hosts: host.docker.internal:host-gateway` → **Linux 下必须显式声明**（Mac/Windows 自动支持）
- `restart: unless-stopped` → 容器崩溃自动重启（生产推荐）
- `5173:80` → 宿主机 5173 映射到前端容器内 Nginx 监听的 80 端口

把这个文件放到 `/home/ubuntu/movie-agent-lab/infra/docker-compose.prod.yml`。

---

### 第五步：首次构建并启动

**5.1 在 tmux 里跑（避免 SSH 断线导致构建中断）**

```bash
tmux new -s deploy        # 新建会话；已有则 tmux attach -t deploy
cd /home/ubuntu/movie-agent-lab/infra
docker compose -f docker-compose.prod.yml up --build -d
```

> **说明**：首次构建很慢（后端 pip 装包 1~3 分钟、前端 npm install + vue-tsc 编译 3~10 分钟），加 `-d` 后台运行，构建完会自动启动容器。tmux 内按 `Ctrl+b` 然后 `d` 退出但保留进程；`tmux attach -t deploy` 重新进入。

**5.2 数据库迁移（创建新表）**

```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

> **说明**：项目用 Alembic 管理数据库结构。新增的表（`chat_sessions`、`chat_messages`、`agent_memories`、`agent_trace`、`recommendation_runs`）需要这一步建出来。**不会修改旧业务表**（actor/movie/rating 等都安全）。如果已是最新版本会显示 "nothing to do"，正常。

**5.3 验证**

```bash
# 后端健康
curl http://127.0.0.1:8000/health
# 期望返回：{"status":"ok","app":"Movie Agent Lab","env":"prod"}

# 前端
curl -I http://127.0.0.1:5173
# 期望返回：HTTP/1.1 200 OK

# 后端能查到电影数据
curl 'http://127.0.0.1:8000/api/v1/movies?limit=3'
# 期望返回 JSON 包含电影列表
```

---

### 第六步：开放云厂商安全组端口

**这一步必做**！上面所有 curl 测试都是在服务器本机访问，浏览器从外网访问还需要：

1. 登录云厂商控制台（腾讯云 https://console.cloud.tencent.com/cvm）
2. 实例 → 安全组 → 编辑入站规则
3. 添加两条规则：
   - 协议 `TCP`，端口 `5173`，来源 `0.0.0.0/0`（前端）
   - 协议 `TCP`，端口 `8000`，来源 `0.0.0.0/0`（后端 API）
4. 保存（立即生效）

**⚠️ 千万不要**放行 3306（MySQL）和 6379（Redis）！否则密码暴露公网。

---

### 第七步：浏览器验证

打开 `http://<服务器公网IP>:5173/login`，F12 打开开发者工具 → Network 标签，点击注册/登录。

正常情况：
- 请求 URL 应该是 `http://<服务器公网IP>:8000/api/v1/auth/login`
- 状态码 200 或 401（账号不存在）

如果 URL 还是 `http://127.0.0.1:8000/...` → 浏览器缓存了旧 JS，**强制清缓存**：
- 电脑：F12 → Network 勾选 **Disable cache** → `Cmd+Shift+R` / `Ctrl+Shift+F5`
- 手机：用无痕模式重新打开

---

## 部署常见坑（实战总结）

| 现象 | 原因 | 解决 |
|---|---|---|
| `docker ps` 报 permission denied | 用户没在 docker 组 | `sudo usermod -aG docker $USER` 然后退出重登 |
| 后端启动报 `Can't connect to MySQL` | `host.docker.internal` 在 Linux 上没生效 | 确认 `docker-compose.prod.yml` 里有 `extra_hosts: host.docker.internal:host-gateway` |
| 后端报 `Access denied for 'root'@'172.17.x.x'` | MySQL 不允许 root 从其他 IP 连 | 给 `root@%` 加权限（见 1.2） |
| 浏览器登录显示 Network Error，URL 是 `127.0.0.1:8000` | 前端 `VITE_API_BASE_URL` 没生效 | 改 `frontend/.env` + `docker compose build --no-cache frontend` 强制重建 |
| 重建前端后浏览器还是旧 URL | 浏览器缓存了旧 JS | F12 勾选 Disable cache，硬刷新或用无痕模式 |
| Alembic 报 `source code string cannot contain null bytes` | 上传过程中 .py 文件损坏 | 用 git clone 而不是 scp 压缩包传整个项目 |
| 浏览器开不了 `http://IP:5173`，本机 curl 能开 | 云厂商安全组没放行端口 | 控制台添加入站规则 TCP 5173 和 8000 |
| CORS 报错 | `CORS_ORIGINS` 不包含浏览器访问的 URL | 加入 `http://<公网IP>:5173`，逗号分隔，**不要空格** |
| 后端启动看到 `env: dev` | `APP_ENV` 没改 | 改 `.env` 里 `APP_ENV=prod`，restart backend |
| `.env` 文件内容拼接错乱（如 `predict` 后面接下一个 key） | nano/vim 编辑时换行丢失 | 在本地 Mac 写好用 scp 覆盖上传 |

---

## 日常运维

### 更新代码后重新部署

**标准三步**：

```bash
ssh ubuntu@43.138.158.143
cd /home/ubuntu/movie-agent-lab && git pull
cd infra
```

然后按**改动范围**选下面一条命令：

| 改动范围 | 命令 |
|---|---|
| 只改后端 Python | `docker compose -f docker-compose.prod.yml up -d --build backend` |
| 只改前端 Vue/TS | `docker compose -f docker-compose.prod.yml build --no-cache frontend && docker compose -f docker-compose.prod.yml up -d frontend` |
| 前后端都改了 | `docker compose -f docker-compose.prod.yml up -d --build` |
| 改了 alembic 迁移 | 上面命令跑完后再加：`docker compose -f docker-compose.prod.yml exec backend alembic upgrade head` |
| 只改了 `.env` | 后端：`docker compose -f docker-compose.prod.yml restart backend`；前端必须 `--no-cache` 重 build |

### 几个易踩的坑

1. **前端必须 `--no-cache`**：`VITE_*` 是构建时静态注入到 JS 文件的，Docker 缓存层会复用旧 JS。少了这个参数，浏览器看到的还是旧版。
2. **后端不需要 `--no-cache`**：Python 代码 COPY 进容器，正常 build 就会带上新代码。
3. **改完前端要硬刷新浏览器**：F12 → Network 勾 Disable cache，或 `Cmd+Shift+R` / `Ctrl+Shift+F5`，否则浏览器用的还是缓存的旧 JS。
4. **改 alembic 迁移别忘 `upgrade head`**：否则新代码访问新表会 500。
5. **`.env` 不会被 git 覆盖**：`.gitignore` 已排除，服务器上的 `backend/.env` 和 `frontend/.env` 是手动 scp 上去的，`git pull` 不会动它们。

### 出问题怎么排查

```bash
# 实时看日志
docker compose -f docker-compose.prod.yml logs backend --tail=50 -f
docker compose -f docker-compose.prod.yml logs frontend --tail=50 -f

# 看容器健康状态
docker compose -f docker-compose.prod.yml ps

# 健康检查
curl http://127.0.0.1:8000/health
```

### 回滚到上一个版本

```bash
git log --oneline -5                # 找回滚目标
git reset --hard <commit_hash>
docker compose -f docker-compose.prod.yml up -d --build
```

### 查看日志

```bash
cd /home/ubuntu/movie-agent-lab/infra
docker compose -f docker-compose.prod.yml logs backend --tail=50 -f
docker compose -f docker-compose.prod.yml logs frontend --tail=50 -f
```

### 重启服务

```bash
docker compose -f docker-compose.prod.yml restart backend
docker compose -f docker-compose.prod.yml restart frontend
```

### 备份数据库

```bash
sudo mysqldump -uroot -p<密码> integratedrecsys > ~/backup-$(date +%Y%m%d).sql
```

---

## 安全清单（部署后必做）

1. ✅ 改服务器 SSH 密码（如果之前在不安全的地方暴露过），最好改用 SSH 密钥登录
2. ✅ `JWT_SECRET_KEY` 改为 `openssl rand -hex 32` 生成的随机值
3. ✅ MySQL 3306、Redis 6379 端口**仅安全组内网放行**，禁止公网访问
4. ✅ 火山引擎 / OpenAI 等 API Key 仅放在 `backend/.env`，不要提交到 GitHub（`.gitignore` 已排除）
5. ✅ 定期备份数据库（`mysqldump` cron 任务）
