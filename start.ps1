<#
.SYNOPSIS
    QuantLab 服务启动脚本 (PowerShell)
    用法: .\start.ps1 [start|status]
.DESCRIPTION
    启动后端 (FastAPI) 和前端 (Vite) 服务。
    假设环境已经配置完毕，如果第一次运行请先执行 .\install.ps1
#>

param([string]$Action = "start")

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PidDir = Join-Path $ProjectRoot ".pids"
$LogDir = Join-Path $ProjectRoot ".logs"

# 创建目录
if (-not (Test-Path $PidDir)) { New-Item -ItemType Directory -Path $PidDir -Force | Out-Null }
if (-not (Test-Path $LogDir))  { New-Item -ItemType Directory -Path $LogDir  -Force | Out-Null }

$BackendPidFile = Join-Path $PidDir "backend.pid"
$FrontendPidFile = Join-Path $PidDir "frontend.pid"
$BackendLog = Join-Path $LogDir "backend.log"
$FrontendLog = Join-Path $LogDir "frontend.log"

$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$PythonBin = Join-Path $BackendDir ".venv\Scripts\python.exe"
$UvicornBin = Join-Path $BackendDir ".venv\Scripts\uvicorn.exe"

$BackendPort = 8000
$FrontendPort = 3000

# 颜色输出
function Info  { Write-Host "[INFO]  " -NoNewline -ForegroundColor Cyan;   Write-Host $args }
function Warn  { Write-Host "[WARN]  " -NoNewline -ForegroundColor Yellow; Write-Host $args }
function Err   { Write-Host "[ERROR] " -NoNewline -ForegroundColor Red;    Write-Host $args }
function Ok    { Write-Host "[OK]    " -NoNewline -ForegroundColor Green;  Write-Host $args }

# =====================================================
# 基础功能
# =====================================================

# 检查进程是否在运行 (通过 PID 文件)
function Test-ProcessRunning($pidFilePath) {
    if (-not (Test-Path $pidFilePath)) { return $false }
    $pid = Get-Content $pidFilePath -Raw 2>$null
    if (-not $pid) { return $false }
    $pid = $pid.Trim()
    if (-not $pid) { return $false }
    $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
    return ($null -ne $proc)
}

# 检查端口是否在监听
function Test-PortListening($port) {
    $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    return ($null -ne $conn)
}

# 获取监听进程的 PID
function Get-ListenerPid($port) {
    $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($conn) { return $conn.OwningProcess }
    return $null
}

# 等待端口就绪
function Wait-ForPort($port, $maxWait = 30) {
    for ($i = 0; $i -lt $maxWait; $i++) {
        try {
            $req = [System.Net.WebRequest]::Create("http://localhost:$port/")
            $req.Timeout = 1000
            $req.GetResponse().Close()
            return $true
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    return $false
}

# 通过 PID 文件停止进程
function Stop-ByPidFile($pidFilePath, $name) {
    if (-not (Test-Path $pidFilePath)) { return }
    $pid = Get-Content $pidFilePath -Raw 2>$null
    if (-not $pid) { Remove-Item $pidFilePath -Force -ErrorAction SilentlyContinue; return }
    $pid = $pid.Trim()
    if (-not $pid) { Remove-Item $pidFilePath -Force -ErrorAction SilentlyContinue; return }

    $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
    if ($proc) {
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
        $proc2 = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($proc2) {
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 1
        }
        Info "$name (PID $pid) 已停止"
    } else {
        if (Test-Path $pidFilePath) {
            Warn "$name PID 文件存在但进程 $pid 不存在，清理"
        }
    }
    Remove-Item $pidFilePath -Force -ErrorAction SilentlyContinue
}

# =====================================================
# 环境快速前置检查
# =====================================================
function Quick-CheckEnv {
    $installedFile = Join-Path $ProjectRoot ".installed"
    if (-not (Test-Path $installedFile)) {
        Warn "环境尚未配置"
        Warn "请先执行: .\install.ps1"
        exit 1
    }

    $missing = $false
    if (-not (Get-Command "python" -ErrorAction SilentlyContinue) -and -not (Get-Command "python3" -ErrorAction SilentlyContinue)) {
        Err "python 未安装"
        $missing = $true
    }
    if (-not (Get-Command "node" -ErrorAction SilentlyContinue)) {
        Err "node 未安装"
        $missing = $true
    }
    if (-not (Test-Path $UvicornBin)) {
        Err "Python uvicorn 未安装（缺少 $UvicornBin）"
        $missing = $true
    }
    $nmDir = Join-Path $FrontendDir "node_modules"
    if (-not (Test-Path $nmDir)) {
        Err "前端依赖未安装（node_modules 不存在）"
        $missing = $true
    }

    if ($missing) {
        Write-Host ""
        Warn "以上依赖缺失，请执行: .\install.ps1"
        exit 1
    }

    Ok "环境快速检查通过"
}

# =====================================================
# 服务启动
# =====================================================

function Start-Backend {
    if (Test-ProcessRunning $BackendPidFile) {
        $pid = Get-Content $BackendPidFile -Raw
        Info "后端已在运行（PID $pid）"
        return
    }

    Info "启动后端（FastAPI, port $BackendPort）..."
    # 清空日志
    "" | Out-File $BackendLog -Force

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $UvicornBin
    $psi.Arguments = "app.main:app --host 0.0.0.0 --port $BackendPort --reload"
    $psi.WorkingDirectory = $BackendDir
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true

    $proc = [System.Diagnostics.Process]::Start($psi)
    $procId = $proc.Id

    # 写入日志
    $proc.StandardOutput.ReadToEnd() | Out-File $BackendLog -Append
    # 但 ReadToEnd 会阻塞，用异步方式更好
    # 简化处理: 直接用 Start-Process

    # 改用更简单的方式
    $p = Start-Process -FilePath $UvicornBin -ArgumentList "app.main:app --host 0.0.0.0 --port $BackendPort --reload" -WorkingDirectory $BackendDir -NoNewWindow -RedirectStandardOutput $BackendLog -RedirectStandardError $BackendLog -PassThru
    Info "  已提交启动（PID $($p.Id)），等待服务就绪..."

    Start-Sleep -Seconds 3

    $listenerPid = Get-ListenerPid $BackendPort
    if ($listenerPid) {
        $listenerPid | Out-File $BackendPidFile -Force
        Info "  实际监听进程（PID $listenerPid）"
    } else {
        $p.Id | Out-File $BackendPidFile -Force
        Warn "  未找到监听端口的子进程，使用父进程 PID $($p.Id)"
    }

    if (Wait-ForPort $BackendPort 30) {
        $pid = Get-Content $BackendPidFile -Raw
        Ok "后端启动成功（PID $pid）-> http://localhost:$BackendPort"
    } else {
        Err "后端启动超时，请查看日志: $BackendLog"
        if ((Get-Item $BackendLog).Length -gt 0) {
            Warn "  最近的日志:"
            Get-Content $BackendLog -Tail 10 | ForEach-Object { Write-Host "    $_" }
        }
    }
}

function Start-Frontend {
    if (Test-ProcessRunning $FrontendPidFile) {
        $pid = Get-Content $FrontendPidFile -Raw
        Info "前端已在运行（PID $pid）"
        return
    }

    Info "启动前端（Vite Dev Server, port $FrontendPort）..."
    "" | Out-File $FrontendLog -Force

    $p = Start-Process -FilePath "npx" -ArgumentList "vite --host 0.0.0.0 --port $FrontendPort" -WorkingDirectory $FrontendDir -NoNewWindow -RedirectStandardOutput $FrontendLog -RedirectStandardError $FrontendLog -PassThru
    $p.Id | Out-File $FrontendPidFile -Force
    Info "  已提交启动（PID $($p.Id)），等待服务就绪..."

    if (Wait-ForPort $FrontendPort 30) {
        Ok "前端启动成功（PID $($p.Id)）-> http://localhost:$FrontendPort"
    } else {
        Err "前端启动超时，请查看日志: $FrontendLog"
        if ((Get-Item $FrontendLog).Length -gt 0) {
            Warn "  最近的日志:"
            Get-Content $FrontendLog -Tail 10 | ForEach-Object { Write-Host "    $_" }
        }
    }
}

# =====================================================
# 数据更新
# =====================================================

function Update-Data {
    if (-not (Test-Path $PythonBin)) {
        Warn "后端 Python 环境不可用，跳过数据更新"
        return
    }

    $fetchScript = Join-Path $BackendDir "scripts\fetch_daily_data.py"
    $rsScript = Join-Path $BackendDir "scripts\calc_sector_rs.py"

    Info "执行数据采集（fetch_daily_data.py）..."
    Push-Location $BackendDir
    & $PythonBin $fetchScript
    if ($LASTEXITCODE -ne 0) { Warn "数据采集失败（可能是网络或 token 问题）" }
    Pop-Location

    Info "执行板块 RS 计算（calc_sector_rs.py）..."
    Push-Location $BackendDir
    & $PythonBin $rsScript
    if ($LASTEXITCODE -ne 0) { Warn "板块 RS 计算失败" }
    Pop-Location

    Ok "数据更新完成"
}

# =====================================================
# 服务停止
# =====================================================

function Stop-Services {
    Info "停止服务..."
    Stop-ByPidFile $FrontendPidFile "前端"
    Stop-ByPidFile $BackendPidFile "后端"
    Start-Sleep -Seconds 1

    Info "清理可能残留的进程..."
    Get-Process -Name "uvicorn" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "vite" } | Stop-Process -Force -ErrorAction SilentlyContinue 2>$null

    # 清理残留端口
    $ports = @($BackendPort, $FrontendPort)
    foreach ($port in $ports) {
        $listenerPid = Get-ListenerPid $port
        if ($listenerPid) {
            Warn "端口 $port 仍被进程 PID $listenerPid 占用，强制杀掉..."
            Stop-Process -Id $listenerPid -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 1
        }
    }

    Remove-Item $BackendPidFile -Force -ErrorAction SilentlyContinue
    Remove-Item $FrontendPidFile -Force -ErrorAction SilentlyContinue

    Ok "服务已全部停止"
}

# =====================================================
# 服务状态
# =====================================================

function Show-Status {
    Write-Host ""
    Write-Host "========== QuantLab 服务状态 =========="

    $backendRunning = Test-ProcessRunning $BackendPidFile
    $frontendRunning = Test-ProcessRunning $FrontendPidFile

    if ($backendRunning) {
        $pid = Get-Content $BackendPidFile -Raw
        Write-Host "  [运行中] 后端 - PID: $pid - http://localhost:$BackendPort"
    } elseif (Test-Path $BackendPidFile) {
        Write-Host "  [异常]   后端 - PID 文件存在但进程已失效，建议运行 stop"
    } else {
        Write-Host "  [已停止] 后端"
    }

    if ($frontendRunning) {
        $pid = Get-Content $FrontendPidFile -Raw
        Write-Host "  [运行中] 前端 - PID: $pid - http://localhost:$FrontendPort"
    } elseif (Test-Path $FrontendPidFile) {
        Write-Host "  [异常]   前端 - PID 文件存在但进程已失效，建议运行 stop"
    } else {
        Write-Host "  [已停止] 前端"
    }

    $backendListen = Test-PortListening $BackendPort
    $frontendListen = Test-PortListening $FrontendPort

    if ($backendListen) {
        $lPid = Get-ListenerPid $BackendPort
        Write-Host "  [端口]   $BackendPort 有进程监听（PID: $lPid）"
    }
    if ($frontendListen) {
        $lPid = Get-ListenerPid $FrontendPort
        Write-Host "  [端口]   $FrontendPort 有进程监听（PID: $lPid）"
    }
    Write-Host "==========================================="
}

# =====================================================
# 打开浏览器
# =====================================================

function Open-Browser {
    $url = "http://localhost:$FrontendPort"
    Info "打开浏览器: $url"
    Start-Process $url
}

# =====================================================
# 入口
# =====================================================

switch ($Action.ToLower()) {
    "start" {
        Write-Host ""
        Write-Host "=============================================="
        Write-Host "  QuantLab 服务启动"
        Write-Host "=============================================="
        Write-Host ""

        Quick-CheckEnv

        $backendUp = Test-PortListening $BackendPort
        $frontendUp = Test-PortListening $FrontendPort

        if ($backendUp)  { Ok "后端已运行（http://localhost:$BackendPort）" }
        if ($frontendUp) { Ok "前端已运行（http://localhost:$FrontendPort）" }

        if (-not $backendUp)  { Start-Backend }
        if (-not $frontendUp) { Start-Frontend }

        Write-Host ""
        Write-Host "============================================" -ForegroundColor Green
        Write-Host "  QuantLab 服务已启动" -ForegroundColor Green
        Write-Host "  前端界面: http://localhost:$FrontendPort" -ForegroundColor Green
        Write-Host "  后端接口: http://localhost:$BackendPort" -ForegroundColor Green
        Write-Host "============================================" -ForegroundColor Green

        Write-Host ""
        Update-Data
        Write-Host ""
        Open-Browser
    }
    "status" {
        Show-Status
    }
    default {
        Write-Host "用法: .\start.ps1 [start|status]"
        Write-Host "  start    启动服务（默认）"
        Write-Host "  status   查看服务状态"
    }
}
