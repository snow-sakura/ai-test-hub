#!/bin/bash
# AI-HUB 后端服务启动脚本
#
# 用法:
#   chmod +x run.sh && ./run.sh      # 启动服务
#   ./run.sh --reload                 # 开发模式（热重载）
#   ./run.sh --help                   # 查看帮助

set -e

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

# 解析参数
RELOAD=""
PORT=""
HOST="0.0.0.0"

# 从 .env 文件读取 APP_PORT（如果存在）
if [ -f "../.env" ]; then
    ENV_PORT=$(grep -E '^APP_PORT=' ../.env | cut -d'=' -f2 | tr -d '[:space:]')
    [ -n "$ENV_PORT" ] && PORT="$ENV_PORT"
fi

while [[ $# -gt 0 ]]; do
    case "$1" in
        --reload) RELOAD="--reload"; shift ;;
        --port) PORT="$2"; shift 2 ;;
        --host) HOST="$2"; shift 2 ;;
        --help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --reload      开发模式，修改代码自动重启"
            echo "  --port PORT   指定端口 (默认: 8000)"
            echo "  --host HOST   指定监听地址 (默认: 0.0.0.0)"
            echo "  --help        显示帮助"
            exit 0
            ;;
        *) echo "未知参数: $1"; exit 1 ;;
    esac
done

# 检查虚拟环境
if [ -d ".venv" ]; then
    echo "📦 激活虚拟环境..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "📦 激活虚拟环境..."
    source venv/bin/activate
fi

echo "🚀 AI-HUB API Server 启动中..."
echo "📡 地址: http://${HOST}:${PORT}"
echo "📋 文档: http://${HOST}:${PORT}/docs"

exec uvicorn app.main:app \
    --host "$HOST" \
    --port "$PORT" \
    $RELOAD \
    --log-level info
