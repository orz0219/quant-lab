#!/usr/bin/env bash
# =============================================
# QuantLab 停止脚本 (stop.sh)
# 用法: ./stop.sh
# =============================================

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
PID_DIR="$PROJECT_ROOT/.pids"

BACKEND_PID_FILE="$PID_DIR/backend.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"
BACKEND_DIR="$PROJECT_ROOT/backend"
BACKEND_PORT=8000
FRONTEND_PORT=3000

info()    { echo -e "\033[1;34m[INFO]\033[0m  $1"; }
warn()    { echo -e "\033[1;33m[WARN]\033[0m  $1"; }
success() { echo -e "\033[1;32m[OK]\033[0m    $1"; }

echo ""
echo "========== 停止 QuantLab 服务 =========="

# 1. 通过 PID 文件停止
if [[ -f "$FRONTEND_PID_FILE" ]]; then
    pid=$(cat "$FRONTEND_PID_FILE" 2>/dev/null)
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null || true
        sleep 1
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null || true
            sleep 1
        fi
        info "前端 (PID $pid) 已停止"
    fi
    rm -f "$FRONTEND_PID_FILE"
fi

if [[ -f "$BACKEND_PID_FILE" ]]; then
    pid=$(cat "$BACKEND_PID_FILE" 2>/dev/null)
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null || true
        sleep 1
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null || true
            sleep 1
        fi
        info "后端 (PID $pid) 已停止"
    fi
    rm -f "$BACKEND_PID_FILE"
fi

# 2. 强制清理残留进程
info "清理残留进程..."
pkill -9 -f "uvicorn app.main" 2>/dev/null || true
pkill -9 -f "$BACKEND_DIR/.venv/bin/uvicorn" 2>/dev/null || true
pkill -9 -f "node server.js" 2>/dev/null || true
pkill -9 -f "vite" 2>/dev/null || true
sleep 2

# 3. 检查端口是否已释放，未释放则用 lsof 精确查杀
if command -v lsof >/dev/null 2>&1; then
    for port in $BACKEND_PORT $FRONTEND_PORT; do
        pid=$(lsof -ti:"$port" -sTCP:LISTEN 2>/dev/null)
        if [[ -n "$pid" ]]; then
            warn "端口 $port 仍被进程 PID $pid 占用，强制杀掉..."
            kill -9 "$pid" 2>/dev/null || true
            sleep 1
        fi
    done
fi

rm -f "$BACKEND_PID_FILE" "$FRONTEND_PID_FILE" 2>/dev/null

# 4. 最终确认
echo ""
echo "========== 确认端口状态 =========="
backend_alive=false
frontend_alive=false
if command -v curl >/dev/null 2>&1; then
    curl -sf "http://localhost:$BACKEND_PORT/" >/dev/null 2>&1 && backend_alive=true
    curl -sf "http://localhost:$FRONTEND_PORT/" >/dev/null 2>&1 && frontend_alive=true
elif command -v lsof >/dev/null 2>&1; then
    lsof -ti:"$BACKEND_PORT" -sTCP:LISTEN >/dev/null 2>&1 && backend_alive=true
    lsof -ti:"$FRONTEND_PORT" -sTCP:LISTEN >/dev/null 2>&1 && frontend_alive=true
fi

if $backend_alive; then
    warn "后端端口 $BACKEND_PORT 仍在运行，建议手动查看"
else
    success "后端端口 $BACKEND_PORT 已释放"
fi

if $frontend_alive; then
    warn "前端端口 $FRONTEND_PORT 仍在运行，建议手动查看"
else
    success "前端端口 $FRONTEND_PORT 已释放"
fi

echo ""
success "服务已全部停止"
