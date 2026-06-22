#!/usr/bin/env bash
# 打包 movie-agent-lab 用于服务器部署（不含 node_modules / .venv）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="$(dirname "$ROOT")"
NAME="movie-agent-lab-deploy"
STAMP="$(date +%Y%m%d-%H%M%S)"
ARCHIVE="${OUT_DIR}/${NAME}-${STAMP}.tar.gz"

cd "$ROOT/.."

tar czf "$ARCHIVE" \
  --exclude='movie-agent-lab/frontend/node_modules' \
  --exclude='movie-agent-lab/frontend/dist' \
  --exclude='movie-agent-lab/backend/.venv' \
  --exclude='movie-agent-lab/**/__pycache__' \
  --exclude='movie-agent-lab/**/.pytest_cache' \
  --exclude='movie-agent-lab/**/.ruff_cache' \
  --exclude='movie-agent-lab/**/.DS_Store' \
  --exclude='movie-agent-lab/backend/.env' \
  --exclude='movie-agent-lab/frontend/.env' \
  movie-agent-lab/

echo "✅ 打包完成: $ARCHIVE"
ls -lh "$ARCHIVE"
