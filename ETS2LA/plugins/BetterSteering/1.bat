@echo off

:: 提升权限，确保以管理员身份运行
:: 检查当前是否具有管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 此脚本需要管理员权限，请使用管理员身份运行。
    pause
    exit /b
)

:: 导航到脚本所在的目录
cd /d "C:\Users\22895\PycharmProjects\pythonProject1\.venv\Scripts"

:: 运行 Python 脚本
python main.py

:: 暂停以查看输出或错误信息
pause