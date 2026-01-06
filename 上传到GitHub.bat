@echo off
chcp 65001 >nul
echo ========================================
echo 上传代码到 GitHub
echo ========================================
echo.

cd /d "%~dp0"

echo [1/6] 初始化 Git 仓库...
git init
echo.

echo [2/6] 添加所有文件...
git add .
echo.

echo [3/6] 提交代码...
git commit -m "Initial commit: Task Reminder System with email API"
echo.

echo [4/6] 准备连接远程仓库...
echo.
echo 请在 GitHub 上创建新仓库：
echo   1. 访问 https://github.com/new
echo   2. 仓库名称：task-reminder
echo   3. 选择 Public
echo   4. 点击 "Create repository"
echo.
echo 创建完成后，按任意键继续...
pause >nul

echo.
set /p GITHUB_USER="请输入你的 GitHub 用户名: "
set /p GITHUB_TOKEN="请输入你的 GitHub Personal Access Token (如果不懂就按回车跳过): "

echo.
echo [5/6] 添加远程仓库...
if "%GITHUB_TOKEN%"=="" (
    git remote add origin https://github.com/%GITHUB_USER%/task-reminder.git
) else (
    git remote add origin https://%GITHUB_TOKEN%@github.com/%GITHUB_USER%/task-reminder.git
)
echo.

echo [6/6] 推送到 GitHub...
git branch -M main
git push -u origin main
echo.

echo ========================================
echo 完成！
echo ========================================
echo.
echo 你的代码已上传到：
echo https://github.com/%GITHUB_USER%/task-reminder
echo.
echo 下一步：
echo 1. 访问 https://render.com
echo 2. 用 GitHub 登录
echo 3. 创建新的 Web Service
echo.
pause
