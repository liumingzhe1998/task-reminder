@echo off
chcp 65001 >nul
echo ========================================
echo 推送邮件修复代码到 GitHub
echo ========================================
echo.

cd /d "%~dp0"

echo 正在推送代码...
git push origin main

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo [成功] 代码已推送！
    echo ========================================
    echo.
    echo Render 会自动重新部署，请等待1-2分钟
    echo 然后修改环境变量：
    echo   EMAIL_SMTP_PORT = 465
    echo.
    pause
    exit 0
) else (
    echo.
    echo ========================================
    echo [失败] 推送失败
    echo ========================================
    echo.
    echo 可能的原因：
    echo 1. 网络连接问题
    echo 2. GitHub 访问受限
    echo.
    echo 建议：
    echo - 稍后重新运行此脚本
    echo - 或检查网络连接
    echo - 或尝试使用手机热点
    echo.
    pause
    exit 1
)
