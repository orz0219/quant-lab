#!/usr/bin/env bash
# =====================================================
# QuantLab 服务启动/停止脚本 (macOS 兼容版)
# 用法: bash start.sh [start|stop|restart|status]
#
# 注: 此脚本假设环境已经配置完毕
#     如果第一次运行，请先执行: bash install.sh
# =====================================================
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
PID_DIR="$PROJECT_ROOT/.pids"
LOG_DIR="$PROJECT_ROOT/.logs"

mkdir -p "$PID_DIR" "$LOG_DIR"

BACKEND_PID_FILE="$PID_DIR/backend.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"

BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

UVICORN_BIN="$BACKEND_DIR/.venv/bin/uvicorn"
NODE_BIN="npx"

BACKEND_PORT=8000
FRONTEND_PORT=3000
PYTHON_BIN="$BACKEND_DIR/.venv/bin/python3"
FETCH_SCRIPT="$BACKEND_DIR/scripts/fetch_daily_data.py"
RS_SCRIPT="$BACKEND_DIR/scripts/calc_sector_rs.py"

# --- 颜色输出 ---
info()    { echo -e "\033[1;34m[INFO]\033[0m  $1"; }
warn()    { echo -e "\033[1;33m[WARN]\033[0m  $1"; }
err()     { echo -e "\033[1;31m[ERROR]\033[0m $1" 1>&2; }
success() { echo -e "\033[1;32m[OK]\033[0m    $1"; }

# =====================================================
# 基础功能
# =====================================================

is_running() {
    local pid_file="$1"
    [[ -f "$pid_file" ]] || return 1
    local pid
    pid="$(cat "$pid_file" 2>/dev/null)"
    [[ -n "$pid" ]] || return 1
    kill -0 "$pid" 2>/dev/null
}

check_port_listening() {
    local port="$1"
    if command -v lsof >/dev/null 2>&1; then
        lsof -ti:"$port" -sTCP:LISTEN >/dev/null 2>&1
    else
        curl -sf "http://localhost:$port/" >/dev/null 2>&1
    fi
}

get_listener_pid() {
    local port="$1"
    if command -v lsof >/dev/null 2>&1; then
        lsof -ti:"$port" -sTCP:LISTEN 2>/dev/null | head -1
    fi
}

kill_pid_file() {
    local pid_file="$1"
    local name="$2"
    if [[ ! -f "$pid_file" ]]; then
        return 0
    fi
    local pid
    pid="$(cat "$pid_file" 2>/dev/null)"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null || true
        sleep 1
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null || true
            sleep 1
        fi
        info "$name (PID $pid) 已停止"
    else
        if [[ -n "$pid" ]]; then
            warn "$name PID 文件存在但进程 $pid 不存在，清理"
        else
            warn "$name PID 文件为空，清理"
        fi
    fi
    rm -f "$pid_file"
}

wait_for_port() {
    local port="$1"
    local max_wait="${2:-30}"
    local i
    for (( i=0; i<max_wait; i++ )); do
        if curl -sf "http://localhost:$port/" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done
    return 1
}

# =====================================================
# 环境快速前置检查
# =====================================================
quick_check_env() {
    # 检查 .installed 标记
    if [[ ! -f "$PROJECT_ROOT/.installed" ]]; then
        warn "环境尚未配置"
        warn "请先执行: bash install.sh"
        exit 1
    fi

    # 检查必要工具和关键文件
    local missing=false

    if ! command -v python3 >/dev/null 2>&1; then
        err "python3 未安装"
        missing=true
    fi
    if ! command -v node >/dev/null 2>&1; then
        err "node 未安装"
        missing=true
    fi
    if [[ ! -x "$UVICORN_BIN" ]]; then
        err "Python uvicorn 未安装（缺少 ${UVICORN_BIN}）"
        missing=true
    fi
    if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
        err "前端依赖未安装（node_modules 不存在）"
        missing=true
    fi

    if $missing; then
        warn ""
        warn "以上依赖缺失，请执行: bash install.sh"
        exit 1
    fi

    success "环境快速检查通过"
}

# =====================================================
# 服务启动
# =====================================================

start_backend() {
    if is_running "$BACKEND_PID_FILE"; then
        info "后端已在运行（PID $(cat "$BACKEND_PID_FILE")）"
        return 0
    fi

    info "启动后端（FastAPI, port ${BACKEND_PORT}）..."
    : > "$BACKEND_LOG"

    nohup bash -c "cd '$BACKEND_DIR' && exec '$UVICORN_BIN' app.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload" >> "$BACKEND_LOG" 2>&1 &
    disown $!
    local parent_pid=$!
    info "  已提交启动（PID ${parent_pid}），等待服务就绪..."

    sleep 3

    local listener_pid
    listener_pid=$(get_listener_pid "$BACKEND_PORT")
    if [[ -n "$listener_pid" ]]; then
        echo "$listener_pid" > "$BACKEND_PID_FILE"
        info "  实际监听进程（PID ${listener_pid}）"
    else
        echo "$parent_pid" > "$BACKEND_PID_FILE"
        warn "  未找到监听端口的子进程，使用父进程 PID $parent_pid"
    fi

    if wait_for_port "$BACKEND_PORT" 30; then
        success "后端启动成功（PID $(cat "$BACKEND_PID_FILE")）-> http://localhost:$BACKEND_PORT"
        return 0
    else
        err "后端启动超时，请查看日志: $BACKEND_LOG"
        if [[ -s "$BACKEND_LOG" ]]; then
            warn "  最近的日志:"
            tail -10 "$BACKEND_LOG" | sed 's/^/    /'
        fi
        return 1
    fi
}

start_frontend() {
    if is_running "$FRONTEND_PID_FILE"; then
        info "前端已在运行（PID $(cat "$FRONTEND_PID_FILE")）"
        return 0
    fi

    info "启动前端（Vite Dev Server, port ${FRONTEND_PORT}）..."
    : > "$FRONTEND_LOG"

    nohup bash -c "cd '$FRONTEND_DIR' && exec $NODE_BIN vite --host 0.0.0.0 --port $FRONTEND_PORT" >> "$FRONTEND_LOG" 2>&1 &
    disown $!
    local pid=$!
    echo "$pid" > "$FRONTEND_PID_FILE"
    info "  已提交启动（PID ${pid}），等待服务就绪..."

    if wait_for_port "$FRONTEND_PORT" 30; then
        success "前端启动成功（PID ${pid}）-> http://localhost:${FRONTEND_PORT}"
        return 0
    else
        err "前端启动超时，请查看日志: $FRONTEND_LOG"
        if [[ -s "$FRONTEND_LOG" ]]; then
            warn "  最近的日志:"
            tail -10 "$FRONTEND_LOG" | sed 's/^/    /'
        fi
        return 1
    fi
}

# =====================================================
# 数据更新
# =====================================================

update_data() {
    if [[ ! -x "$PYTHON_BIN" ]]; then
        warn "后端 Python 环境不可用，跳过数据更新"
        return 1
    fi

    info "执行数据采集（fetch_daily_data.py）..."
    cd "$BACKEND_DIR"
    "$PYTHON_BIN" "$FETCH_SCRIPT" || warn "数据采集失败（可能是网络或 token 问题）"
    cd "$PROJECT_ROOT"

    info "执行板块 RS 计算（calc_sector_rs.py）..."
    cd "$BACKEND_DIR"
    "$PYTHON_BIN" "$RS_SCRIPT" || warn "板块 RS 计算失败"
    cd "$PROJECT_ROOT"

    success "数据更新完成"
}

# =====================================================
# 服务停止
# =====================================================

stop_services() {
    info "停止服务..."

    kill_pid_file "$FRONTEND_PID_FILE" "前端"
    kill_pid_file "$BACKEND_PID_FILE" "后端"

    sleep 1

    info "清理可能残留的进程..."
    pkill -9 -f "uvicorn app.main" 2>/dev/null || true
    pkill -9 -f "node server.js" 2>/dev/null || true
    pkill -9 -f "vite" 2>/dev/null || true
    pkill -9 -f "$BACKEND_DIR/.venv/bin/uvicorn" 2>/dev/null || true

    rm -f "$BACKEND_PID_FILE" "$FRONTEND_PID_FILE"

    success "服务已全部停止"
}

# =====================================================
# 服务状态
# =====================================================

show_status() {
    echo ""
    echo "========== QuantLab 服务状态 =========="
    if is_running "$BACKEND_PID_FILE"; then
        echo "  [运行中] 后端 - PID: $(cat "$BACKEND_PID_FILE") - http://localhost:$BACKEND_PORT"
    elif [[ -f "$BACKEND_PID_FILE" ]]; then
        echo "  [异常]   后端 - PID 文件存在但进程已失效，建议运行 $0 stop"
    else
        echo "  [已停止] 后端"
    fi

    if is_running "$FRONTEND_PID_FILE"; then
        echo "  [运行中] 前端 - PID: $(cat "$FRONTEND_PID_FILE") - http://localhost:$FRONTEND_PORT"
    elif [[ -f "$FRONTEND_PID_FILE" ]]; then
        echo "  [异常]   前端 - PID 文件存在但进程已失效，建议运行 $0 stop"
    else
        echo "  [已停止] 前端"
    fi

    if check_port_listening "$BACKEND_PORT"; then
        local l_pid
        l_pid=$(get_listener_pid "$BACKEND_PORT")
        echo "  [端口]   $BACKEND_PORT 有进程监听（PID: ${l_pid:-未知}）"
    fi
    if check_port_listening "$FRONTEND_PORT"; then
        local l_pid
        l_pid=$(get_listener_pid "$FRONTEND_PORT")
        echo "  [端口]   $FRONTEND_PORT 有进程监听（PID: ${l_pid:-未知}）"
    fi
    echo "==========================================="
}

# =====================================================
# 打开浏览器
# =====================================================

open_browser() {
    local url="http://localhost:$FRONTEND_PORT"
    if command -v open >/dev/null 2>&1; then
        info "打开浏览器: $url"
        open "$url"
    else
        info "请手动打开浏览器访问: $url"
    fi
}

# =====================================================
# 启动逻辑
# =====================================================

do_start() {
    echo ""
    echo "=============================================="
    echo "  QuantLab 服务启动"
    echo "=============================================="
    echo ""

    # 快速前置检查（缺失则提示运行 install.sh）
    quick_check_env

    # 端口判断，已经启动的就跳过
    local backend_up=false
    local frontend_up=false

    if check_port_listening "$BACKEND_PORT"; then
        backend_up=true
        success "后端已运行（http://localhost:${BACKEND_PORT}）"
    fi

    if check_port_listening "$FRONTEND_PORT"; then
        frontend_up=true
        success "前端已运行（http://localhost:${FRONTEND_PORT}）"
    fi

    ! $backend_up  && start_backend  || true
    ! $frontend_up && start_frontend || true

    echo ""
    success "============================================"
    success "  QuantLab 服务已启动"
    success "  前端界面: http://localhost:$FRONTEND_PORT"
    success "  后端接口: http://localhost:$BACKEND_PORT"
    success "============================================"

    # 更新数据 + 打开浏览器
    echo ""
    update_data
    echo ""
    open_browser
}

# =====================================================
# 命令分发
# =====================================================

case "${1:-start}" in
    start)
        do_start
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        sleep 2
        do_start
        ;;
    status)
        show_status
        ;;
    help|-h|--help)
        echo "QuantLab 服务启动脚本（macOS 兼容版）"
        echo ""
        echo "用法: $0 [start|stop|restart|status]"
        echo ""
        echo "  start    启动服务（默认）"
        echo "  stop     停止服务"
        echo "  restart  重启服务"
        echo "  status   查看服务状态"
        echo ""
        echo "第一次运行？请先执行: bash install.sh"
        ;;
    *)
        err "未知命令: $1"
        echo "用法: $0 [start|stop|restart|status]"
        exit 1
        ;;
esac
