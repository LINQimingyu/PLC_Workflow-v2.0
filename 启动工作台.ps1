param([int]$Port = 8772, [switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$taskApp = Join-Path $taskRoot 'app'
$taskPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
$taskWorkspace = Join-Path $taskRoot 'workspace'
$taskLocal = Join-Path $taskWorkspace '.local'
if (-not (Test-Path -LiteralPath $taskPython)) { throw '请先运行 安装与构建.ps1。' }
New-Item -ItemType Directory -Force -Path $taskLocal | Out-Null
$taskPidFile = Join-Path $taskLocal 'server.pid'
$taskUrlFile = Join-Path $taskLocal 'login-url.txt'
$taskRunning = $null
if (Test-Path -LiteralPath $taskPidFile) {
    $taskSavedPid = [int](Get-Content -LiteralPath $taskPidFile -Raw)
    $taskCandidate = Get-Process -Id $taskSavedPid -ErrorAction SilentlyContinue
    if ($taskCandidate) {
        $taskCommandLine = (Get-CimInstance Win32_Process -Filter "ProcessId=$taskSavedPid").CommandLine
        if ($taskCommandLine -like '*cim.launch*' -and $taskCommandLine.Contains($taskWorkspace)) {
            if ($taskCommandLine -notlike "*--port $Port *") { throw '工作台已在其他端口运行，请使用当前端口。' }
            $taskRunning = $taskCandidate
        }
    }
}
$taskStartedAt = $null
if (-not $taskRunning) {
    if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) { throw '端口已被其他服务占用，请指定另一个 Port。' }
    $env:PYTHONPATH = Join-Path $taskApp 'src'
    $env:PYTHONUTF8 = '1'
    $taskArguments = @('-m', 'cim.launch', '--port', "$Port", '--workspace', ('"' + $taskWorkspace + '"'))
    $taskStartedAt = [DateTime]::UtcNow
    $taskRunning = Start-Process -FilePath $taskPython -WorkingDirectory $taskApp -ArgumentList $taskArguments -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $taskLocal 'server.stdout.log') -RedirectStandardError (Join-Path $taskLocal 'server.stderr.log')
}
$taskReady = $false
for ($taskTry = 0; $taskTry -lt 100; $taskTry++) {
    if ($taskRunning.HasExited) { throw '服务未启动，请检查 workspace\.local\server.stderr.log。' }
    try {
        $taskHealth = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/health" -TimeoutSec 2
        $taskUrlReady = (Test-Path -LiteralPath $taskUrlFile) -and (($null -eq $taskStartedAt) -or ((Get-Item -LiteralPath $taskUrlFile).LastWriteTimeUtc -ge $taskStartedAt))
        if ($taskHealth.application -eq 'gxworks-agent' -and $taskUrlReady) { $taskReady = $true; break }
    } catch { }
    Start-Sleep -Milliseconds 200
}
if (-not $taskReady) { throw '服务尚未就绪，请检查服务日志。' }
Write-Output "工作台已启动：http://127.0.0.1:$Port/#cim"
if (-not $NoBrowser) { Start-Process -FilePath (Get-Content -LiteralPath $taskUrlFile -Raw) }
