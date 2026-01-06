@echo off
chcp 65001 >nul
echo ====================================
echo 任务提醒系统 - 启动脚本
echo ====================================
echo.

echo 请选择要启动的服务：
echo [1] Web服务器 (访问 http://127.0.0.1:5000)
echo [2] 定时邮件提醒服务
echo [3] 退出
echo.

set /p choice=请输入选项 (1-3):

if "%choice%"=="1" (
    echo.
    echo 正在启动Web服务器...
    echo 按 Ctrl+C 停止服务器
    echo.
    python app.py
) else if "%choice%"=="2" (
    echo.
    echo 正在启动定时邮件提醒服务...
    echo 默认每天早上8点发送邮件
    echo 按 Ctrl+C 停止服务
    echo.
    python scheduler.py
) else if "%choice%"=="3" (
    exit
) else (
    echo 无效选项，请重新运行脚本
    pause
)
