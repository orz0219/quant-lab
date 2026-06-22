#!/usr/bin/env bash
# ============================================================
# QuantLab 环境安装与配置脚本
# 用法: bash install.sh
#
# 检测并自动配置所有依赖:
#   1. 系统工具: python3, node, curl
#   2. Python 虚拟环境 + pip 依赖 (requirements.txt 全量)
#   3. Node 依赖 (package.json)
#   4. Tushare Token (通过 config.py 检测, 未配置则交互引导)
# ============================================================
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
PYTHON_BIN="$BACKEND_DIR/.venv/bin/python3"
PIP_BIN="$BACKEND_DIR/.venv/bin/pip"

# --- 颜色输出 ---
info()    { echo -e "\033[1;34m[INFO]\033[0m  $1"; }
warn()    { echo -e "\033[1;33m[WARN]\033[0m  $1"; }
err()     { echo -e "\033[1;31m[ERROR]\033[0m $1" 1>&2; }
success() { echo -e "\033[1;32m[OK]\033[0m    $1"; }
section() { echo -e "\n\033[1;36m========== $1 ==========\033[0m"; }

# =====================================================
# 第一阶段: 系统工具检查
# =====================================================
check_system_tools() {
    section "系统工具检测"

    local ok=true

    if ! command -v python3 >/dev/null 2>&1; then
        err "python3 未安装"
        echo "   → 解决: https://www.python.org/downloads/ 安装 Python 3.10+"
        ok=false
    else
        success "Python3: $(python3 --version 2>&1)"
    fi

    if ! command -v node >/dev/null 2>&1; then
        err "node 未安装"
        echo "   → 解决: https://nodejs.org/ 安装 Node.js 18+"
        ok=false
    else
        success "Node:    $(node --version 2>&1)"
    fi

    if ! command -v curl >/dev/null 2>&1; then
        err "curl 未安装"
        echo "   → 解决: macOS: brew install curl  |  Linux: apt install curl"
        ok=false
    else
        success "curl:    已就绪"
    fi

    $ok || { err "以上必要工具缺失，请安装后重试"; exit 1; }
    echo ""
}

# =====================================================
# 第二阶段: Python 环境
# =====================================================
setup_python_env() {
    section "Python 环境配置"

    # 1. 创建虚拟环境
    if [[ ! -f "$PYTHON_BIN" ]]; then
        info "Python 虚拟环境不存在，正在创建..."
        (cd "$BACKEND_DIR" && python3 -m venv .venv) || {
            err "虚拟环境创建失败"
            exit 1
        }
        success "虚拟环境已创建"
    else
        info "Python 虚拟环境已存在（跳过）"
    fi

    # 2. 升级 pip
    info "更新 pip 至最新版本..."
    "$PIP_BIN" install --upgrade pip -q || warn "pip 升级失败（可忽略）"

    # 3. 安装/更新依赖 (pip 自身是幂等的，重复执行无副作用)
    info "安装后端 Python 依赖 (requirements.txt)..."
    "$PIP_BIN" install -r "$BACKEND_DIR/requirements.txt" || {
        err "Python 依赖安装失败"
        echo "   → 解决: 检查网络或版本冲突"
        exit 1
    }
    success "Python 依赖安装完成"
    echo ""
}

# =====================================================
# 第三阶段: Python 依赖全量验证
# =====================================================
verify_python_deps() {
    section "Python 依赖验证"

    # 解析 requirements.txt 中的包名（跳过注释和空行）
    local packages=()
    while IFS= read -r line; do
        line="${line%%#*}"                # 去掉注释
        line="$(echo "$line" | xargs)"    # 去首尾空格
        [[ -z "$line" ]] && continue
        # 去掉版本约束，只取包名（第一段）
        local pkg="${line%%[><=!\[\]]*}"
        pkg="$(echo "$pkg" | xargs)"
        [[ -n "$pkg" ]] && packages+=("$pkg")
    done < "$BACKEND_DIR/requirements.txt"

    # 转换为 Python import 名
    local all_ok=true
    for pkg in "${packages[@]}"; do
        # 特殊映射: 包名 → import 名
        case "$pkg" in
            Pillow)          import_name="PIL" ;;
            python-dotenv)   import_name="dotenv" ;;
            uvicorn|uvicorn*) import_name="uvicorn" ;;
            *)               import_name="$pkg" ;;
        esac
        if (
            cd "$BACKEND_DIR"
            "$PYTHON_BIN" -c "import $import_name" 2>/dev/null
        ); then
            success "  $pkg -> OK"
        else
            err "  $pkg -> 缺失 (import $import_name 失败)"
            all_ok=false
        fi
    done

    $all_ok || {
        err "部分 Python 依赖缺失，正在重新安装..."
        "$PIP_BIN" install -r "$BACKEND_DIR/requirements.txt" || {
            err "重新安装失败，请检查网络"
            exit 1
        }
        success "重新安装完成"
    }
    echo ""
}

# =====================================================
# 第四阶段: Node 依赖
# =====================================================
setup_frontend_deps() {
    section "前端依赖配置"

    if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
        info "node_modules 不存在，正在安装前端依赖..."
        (cd "$FRONTEND_DIR" && npm install) || {
            err "npm install 失败"
            echo "   → 解决: 检查网络或 package.json 错误"
            exit 1
        }
        success "前端依赖安装完成"
    else
        # 检测关键包是否可用
        info "检测前端关键依赖..."
        local core_pkgs=("vue" "vue-router" "echarts" "vite")
        local need_install=false
        for pkg in "${core_pkgs[@]}"; do
            if [[ ! -d "$FRONTEND_DIR/node_modules/$pkg" ]]; then
                warn "  $pkg 缺失"
                need_install=true
            fi
        done
        if $need_install; then
            info "部分依赖缺失，执行 npm install..."
            (cd "$FRONTEND_DIR" && npm install) || {
                err "npm install 失败"
                exit 1
            }
            success "npm install 完成"
        else
            success "前端依赖已就绪"
        fi
    fi
    echo ""
}

# =====================================================
# 第五阶段: Tushare Token 检测
# =====================================================
check_tushare_token() {
    section "Tushare Token 配置"

    # 通过 Python config.py 检测（复用 load_dotenv + os.getenv）
    if (
        cd "$BACKEND_DIR"
        "$PYTHON_BIN" -c "from app.core.config import settings; assert settings.TUSHARE_TOKEN, ''"
    ) 2>/dev/null; then
        local masked
        masked=$(
            cd "$BACKEND_DIR"
            "$PYTHON_BIN" -c "from app.core.config import settings; t=settings.TUSHARE_TOKEN; print(t[:8]+'...')"
        )
        success "Tushare Token 已配置: $masked"
        return 0
    fi

    # 未配置 → 交互引导
    warn "Tushare Token 未配置（数据采集将无法运行）"
    echo ""
    echo "=============================================="
    echo "  请输入您的 Tushare Pro Token"
    echo "  获取地址: https://tushare.pro -> 个人信息"
    echo "=============================================="
    read -p "  Token (直接回车跳过): " input_token

    local env_file="$BACKEND_DIR/.env"
    if [[ -z "$input_token" ]]; then
        warn "  跳过 token 设置，你可之后手动编辑:"
        warn "  $env_file"
        echo "  添加: TUSHARE_TOKEN=你的_token"
        return 1
    fi

    echo "TUSHARE_TOKEN=$input_token" > "$env_file"
    success "Tushare Token 已保存至 $env_file"

    # 验证写入是否有效
    if (
        cd "$BACKEND_DIR"
        "$PYTHON_BIN" -c "from app.core.config import settings; assert settings.TUSHARE_TOKEN, ''"
    ) 2>/dev/null; then
        success "token 验证通过"
    else
        warn "token 已写入但验证失败（可能需要重新运行 install.sh）"
    fi
    echo ""
}

# =====================================================
# 完成标记
# =====================================================
mark_installed() {
    # 写入一个基础信息标记，供 start.sh 快速参考
    cat > "$PROJECT_ROOT/.installed" <<-EOF
# QuantLab install mark
# DO NOT EDIT
install_time="$(date '+%Y-%m-%d %H:%M:%S')"
python_ver="$("$PYTHON_BIN" --version 2>/dev/null || echo 'unknown')"
node_ver="$(node --version 2>/dev/null || echo 'unknown')"
EOF
    success "环境配置完成（标记已写入 .installed）"
}

# =====================================================
# 主函数
# =====================================================
main() {
    echo ""
    echo "=============================================="
    echo "  QuantLab 环境安装程序"
    echo "=============================================="
    echo ""

    check_system_tools
    setup_python_env
    verify_python_deps
    setup_frontend_deps
    check_tushare_token
    mark_installed

    echo ""
    success "============================================"
    success "  环境安装完毕！"
    success "  现在可以运行: bash start.sh"
    success "============================================"
    echo ""
}

main
