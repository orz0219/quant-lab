<#
.SYNOPSIS
    QuantLab 环境安装与配置脚本 (PowerShell)
    用法: .\install.ps1
.DESCRIPTION
    检测并自动配置所有依赖:
    1. 系统工具: python, node
    2. Python 虚拟环境 + pip 依赖 (requirements.txt 全量)
    3. Node 依赖 (package.json)
    4. Tushare Token (通过 config.py 检测, 未配置则交互引导)
#>

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$PythonBin = Join-Path $BackendDir ".venv\Scripts\python.exe"
$PipBin = Join-Path $BackendDir ".venv\Scripts\pip.exe"

# 颜色输出
function Info  { Write-Host "[INFO]  " -NoNewline -ForegroundColor Cyan;   Write-Host $args }
function Warn  { Write-Host "[WARN]  " -NoNewline -ForegroundColor Yellow; Write-Host $args }
function Err   { Write-Host "[ERROR] " -NoNewline -ForegroundColor Red;    Write-Host $args }
function Ok    { Write-Host "[OK]    " -NoNewline -ForegroundColor Green;  Write-Host $args }
function Section { Write-Host "`n========== $args ==========" -ForegroundColor DarkCyan }

# =====================================================
# 第一阶段: 系统工具检查
# =====================================================
function Check-SystemTools {
    Section "系统工具检测"
    $ok = $true

    # 检查 Python (优先 python3, 回退 python)
    $pythonCmd = if (Get-Command "python3" -ErrorAction SilentlyContinue) { "python3" } elseif (Get-Command "python" -ErrorAction SilentlyContinue) { "python" } else { $null }
    if (-not $pythonCmd) {
        Err "python 未安装"
        Write-Host "   → 解决: https://www.python.org/downloads/ 安装 Python 3.10+ (安装时勾选 Add to PATH)"
        $ok = $false
    } else {
        $ver = & $pythonCmd --version 2>&1
        Ok "Python: $ver"
        # 保存供后续使用
        $script:PythonSystemCmd = $pythonCmd
    }

    if (-not (Get-Command "node" -ErrorAction SilentlyContinue)) {
        Err "node 未安装"
        Write-Host "   → 解决: https://nodejs.org/ 安装 Node.js 18+"
        $ok = $false
    } else {
        $ver = node --version 2>&1
        Ok "Node:  $ver"
    }

    if (-not (Get-Command "npm" -ErrorAction SilentlyContinue)) {
        Err "npm 未安装"
        Write-Host "   → 解决: 安装 Node.js 时会自动包含 npm"
        $ok = $false
    } else {
        Ok "npm:   已就绪"
    }

    if (-not $ok) { throw "以上必要工具缺失，请安装后重试" }
    Write-Host ""
}

# =====================================================
# 第二阶段: Python 环境
# =====================================================
function Setup-PythonEnv {
    Section "Python 环境配置"

    # 1. 创建虚拟环境
    if (-not (Test-Path $PythonBin)) {
        Info "Python 虚拟环境不存在，正在创建..."
        Push-Location $BackendDir
        try {
            & $script:PythonSystemCmd -m venv .venv
            if (-not (Test-Path $PythonBin)) { throw "虚拟环境创建失败" }
        } finally { Pop-Location }
        Ok "虚拟环境已创建"
    } else {
        Info "Python 虚拟环境已存在（跳过）"
    }

    # 2. 升级 pip
    Info "更新 pip 至最新版本..."
    & $PipBin install --upgrade pip -q 2>$null
    if ($LASTEXITCODE -ne 0) { Warn "pip 升级失败（可忽略）" }

    # 3. 安装/更新依赖
    $reqTxt = Join-Path $BackendDir "requirements.txt"
    Info "安装后端 Python 依赖 (requirements.txt)..."
    & $PipBin install -r $reqTxt
    if ($LASTEXITCODE -ne 0) { throw "Python 依赖安装失败，请检查网络或版本冲突" }
    Ok "Python 依赖安装完成"
    Write-Host ""
}

# =====================================================
# 第三阶段: Python 依赖全量验证
# =====================================================
function Verify-PythonDeps {
    Section "Python 依赖验证"

    $reqTxt = Join-Path $BackendDir "requirements.txt"
    $packages = @()
    Get-Content $reqTxt | ForEach-Object {
        $line = $_ -replace '#.*$', ''   # 去掉注释
        $line = $line.Trim()
        if (-not $line) { return }
        # 去掉版本约束
        $pkg = $line -replace '[><=!\[\]].*$', ''
        $pkg = $pkg.Trim()
        if ($pkg) { $packages += $pkg }
    }

    $allOk = $true
    foreach ($pkg in $packages) {
        # 包名 → import 名映射
        $importName = switch -Regex ($pkg) {
            '^Pillow'     { 'PIL' }
            '^python-dotenv' { 'dotenv' }
            '^uvicorn'    { 'uvicorn' }
            default       { $pkg }
        }
        Push-Location $BackendDir
        $ok2 = & $PythonBin -c "import $importName" 2>$null
        Pop-Location
        if ($LASTEXITCODE -eq 0) {
            Ok "  $pkg -> OK"
        } else {
            Err "  $pkg -> 缺失 (import $importName 失败)"
            $allOk = $false
        }
    }

    if (-not $allOk) {
        Warn "部分 Python 依赖缺失，正在重新安装..."
        & $PipBin install -r $reqTxt
        if ($LASTEXITCODE -ne 0) { throw "重新安装失败，请检查网络" }
        Ok "重新安装完成"
    }
    Write-Host ""
}

# =====================================================
# 第四阶段: Node 依赖
# =====================================================
function Setup-FrontendDeps {
    Section "前端依赖配置"

    $nmDir = Join-Path $FrontendDir "node_modules"
    if (-not (Test-Path $nmDir)) {
        Info "node_modules 不存在，正在安装前端依赖..."
        Push-Location $FrontendDir
        try { npm install } finally { Pop-Location }
        if ($LASTEXITCODE -ne 0) { throw "npm install 失败，请检查网络或 package.json 错误" }
        Ok "前端依赖安装完成"
    } else {
        Info "检测前端关键依赖..."
        $corePkgs = @("vue", "vue-router", "echarts", "vite")
        $needInstall = $false
        foreach ($pkg in $corePkgs) {
            $pkgDir = Join-Path $nmDir $pkg
            if (-not (Test-Path $pkgDir)) {
                Warn "  $pkg 缺失"
                $needInstall = $true
            }
        }
        if ($needInstall) {
            Info "部分依赖缺失，执行 npm install..."
            Push-Location $FrontendDir
            try { npm install } finally { Pop-Location }
            if ($LASTEXITCODE -ne 0) { throw "npm install 失败" }
            Ok "npm install 完成"
        } else {
            Ok "前端依赖已就绪"
        }
    }
    Write-Host ""
}

# =====================================================
# 第五阶段: Tushare Token 检测
# =====================================================
function Check-TushareToken {
    Section "Tushare Token 配置"

    # 通过 Python config.py 检测
    Push-Location $BackendDir
    $tokenOk = & $PythonBin -c "from app.core.config import settings; assert settings.TUSHARE_TOKEN, ''" 2>$null
    Pop-Location
    if ($LASTEXITCODE -eq 0) {
        Push-Location $BackendDir
        $masked = & $PythonBin -c "from app.core.config import settings; t=settings.TUSHARE_TOKEN; print(t[:8]+'...')" 2>$null
        Pop-Location
        Ok "Tushare Token 已配置: $masked"
        return
    }

    Warn "Tushare Token 未配置（数据采集将无法运行）"
    Write-Host ""
    Write-Host "=============================================="
    Write-Host "  请输入您的 Tushare Pro Token"
    Write-Host "  获取地址: https://tushare.pro -> 个人信息"
    Write-Host "=============================================="
    $inputToken = Read-Host "  Token (直接回车跳过)"

    $envFile = Join-Path $BackendDir ".env"
    if ([string]::IsNullOrWhiteSpace($inputToken)) {
        Warn "  跳过 token 设置，你可之后手动编辑:"
        Warn "  $envFile"
        Write-Host "  添加: TUSHARE_TOKEN=你的_token"
        return
    }

    "TUSHARE_TOKEN=$inputToken" | Out-File -FilePath $envFile -Encoding ASCII
    Ok "Tushare Token 已保存至 $envFile"

    # 验证
    Push-Location $BackendDir
    & $PythonBin -c "from app.core.config import settings; assert settings.TUSHARE_TOKEN, ''" 2>$null
    Pop-Location
    if ($LASTEXITCODE -eq 0) {
        Ok "token 验证通过"
    } else {
        Warn "token 已写入但验证失败（可能需要重新运行 install.ps1）"
    }
    Write-Host ""
}

# =====================================================
# 完成标记
# =====================================================
function Mark-Installed {
    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $pyVer = & $PythonBin --version 2>$null
    if (-not $pyVer) { $pyVer = "unknown" }
    $nodeVer = node --version 2>$null
    if (-not $nodeVer) { $nodeVer = "unknown" }

    @"
# QuantLab install mark
# DO NOT EDIT
install_time="$now"
python_ver="$pyVer"
node_ver="$nodeVer"
"@ | Out-File -FilePath (Join-Path $ProjectRoot ".installed") -Encoding ASCII

    Ok "环境配置完成（标记已写入 .installed）"
}

# =====================================================
# 主函数
# =====================================================
try {
    Write-Host ""
    Write-Host "=============================================="
    Write-Host "  QuantLab 环境安装程序"
    Write-Host "=============================================="
    Write-Host ""

    Check-SystemTools
    Setup-PythonEnv
    Verify-PythonDeps
    Setup-FrontendDeps
    Check-TushareToken
    Mark-Installed

    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  环境安装完毕！" -ForegroundColor Green
    Write-Host "  现在可以运行: .\start.ps1" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""

    # 暂停，让用户看到结果
    Write-Host "按任意键退出..." -NoNewline
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
} catch {
    Write-Host ""
    Err "安装失败: $_"
    Write-Host "按任意键退出..." -NoNewline
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}
