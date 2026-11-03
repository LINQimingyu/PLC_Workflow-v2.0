param([switch]$SeedExamples)
$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$taskApp = Join-Path $taskRoot 'app'
$taskPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
function Assert-TaskExit { if ($LASTEXITCODE -ne 0) { throw '命令失败，停止安装；请查看上方错误。' } }
if (-not (Test-Path -LiteralPath $taskPython)) { python -m venv (Join-Path $taskRoot '.venv'); Assert-TaskExit }
Push-Location $taskApp
try {
    & $taskPython -m pip install -r requirements/factory-win-py313.lock.txt
    Assert-TaskExit
    & $taskPython scripts/build_factory_catalog.py
    Assert-TaskExit
    if ($SeedExamples) { & $taskPython scripts/seed_factory_workspace.py; Assert-TaskExit }
    Push-Location web
    try { npm ci --no-audit --no-fund; Assert-TaskExit; npm run build; Assert-TaskExit } finally { Pop-Location }
} finally { Pop-Location }
Write-Output '安装与构建完成。运行 启动工作台.ps1。'
