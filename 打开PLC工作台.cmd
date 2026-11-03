@echo off
setlocal
chcp 65001 >nul
title PLC 工作台

set "PLC_LAUNCHER=%~dp0启动工作台.ps1"
if not exist "%PLC_LAUNCHER%" (
    echo 找不到工作台启动脚本。
    echo 请将本文件放在 PLC_Workflow v2.0 文件夹内。
    pause
    exit /b 1
)

echo 正在启动工作台，服务就绪后将自动打开浏览器，请稍候……
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PLC_LAUNCHER%" %*
if errorlevel 1 (
    echo.
    echo 工作台未能打开，请查看上方提示。
    echo 服务日志位于 workspace\.local 文件夹。
    pause
    exit /b 1
)
exit /b 0
