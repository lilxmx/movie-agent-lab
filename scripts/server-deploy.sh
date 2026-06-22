#!/usr/bin/env bash
# 在服务器上解压后执行：bash scripts/server-deploy.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# 首次部署：从 example 复制 .env
if [[ ! -f backend/.env ]]; then
  cp backend/.env.example backend/.env
  echo "⚠️  已创建 backend/.env，请编辑 DB / JWT / LLM / CORS 后再启动"
fi
if [[ ! -f frontend/.env ]]; then
  cp frontend/.env.example frontend/.env
  echo "⚠️  已创建 frontend/.env，请设置 VITE_API_BASE_URL 后再 build"
fi

mkdir -p infra/mysql/init

echo ">>> 启动 Docker Compose..."
cd infra
docker compose up --build -d

echo ">>> 等待后端就绪..."
sleep 8

echo ">>> 运行数据库迁移..."
docker compose exec -T backend alembic upgrade head

echo ""
echo "✅ 部署完成"
echo "   前端: http://$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}'):5173"
echo "   后端: http://$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}'):8000/docs"
echo "   健康: curl http://127.0.0.1:8000/health"
