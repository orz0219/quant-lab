<#
.SYNOPSIS
    QuantLab 服务停止脚本 (PowerShell)
    用法: .\stop.ps1
.DESCRIPTION
    停止后端 (FastAPI) 和前端 (Vite) 服务，清理残留进程和端口。
#>

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PidDir = Join-Path $ProjectRoot ".pids"
$BackendPidFile = Join-Path $PidDir "backend.pid"
$FrontendPidFile = Join-Path $PidDir "frontend.pid"
$BackendDir = Join-Path $ProjectRoot "backend"
$BackendPort = 8000
$FrontendPort = 3000

function Info  { Write-Host "[INFO]  " -NoNewline -ForegroundColor Cyan;   Write-Host $args }
function Warn  { Write-Host "[WARN]  " -NoNewline -ForegroundColor Yellow; Write-Host $args }
function Ok    { Write-Host "[OK]    " -NoNewline -ForegroundColor Green;  Write-Host $args }

Write-Host ""
Write-Host "========== 停止 QuantLab 服务 =========="

# 1. 通过 PID 文件停止进程
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

Stop-ByPidFile $FrontendPidFile "前端"
Stop-ByPidFile $BackendPidFile "后端"

# 2. 强制清理残留进程
Info "清理残留进程..."
Get-Process -Name "uvicorn" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "vite" } | Stop-Process -Force -ErrorAction SilentlyContinue 2>$null
Start-Sleep -Seconds 2

# 3. 检查端口是否已释放，未释放则强制杀掉
function Get-ListenerPid($port) {
    $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($conn) { return $conn.OwningProcess }
    return $null
}

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

# 4. 最终确认
Write-Host ""
Write-Host "========== 确认端口状态 =========="
$backendAlive = $null -ne (Get-ListenerPid $BackendPort)
$frontendAlive = $null -ne (Get-ListenerPid $FrontendPort)

if ($backendAlive) {
    Warn "后端端口 $BackendPort 仍在运行，建议手动查看"
} else {
    Ok "后端端口 $BackendPort 已释放"
}

if ($frontendAlive) {
    Warn "前端端口 $FrontendPort 仍在运行，建议手动查看"
} else {
    Ok "前端端口 $FrontendPort 已释放"
}

Write-Host ""
Ok "服务已全部停止"

# 暂停，让用户看到结果
Write-Host "按任意键退出..." -NoNewline
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
