@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title RedOps 启动器

echo ========================================
echo      RedOps 渗透测试Agent
echo ========================================
echo.

REM 检查Python
echo [*] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] 未找到Python，正在安装...
    echo [!] 请先安装Python 3.8+: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "delims=" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
echo [+] Python版本: !PYTHON_VER!

REM 定义检查函数（通过pip show）
echo.
echo [*] 检查依赖...

REM 检查并安装FastAPI
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [*] 安装 FastAPI...
    pip install fastapi -q
) else (
    echo [+] FastAPI 已安装
)

REM 检查并安装Uvicorn
pip show uvicorn >nul 2>&1
if errorlevel 1 (
    echo [*] 安装 Uvicorn...
    pip install uvicorn -q
) else (
    echo [+] Uvicorn 已安装
)

REM 检查并安装Pydantic
pip show pydantic >nul 2>&1
if errorlevel 1 (
    echo [*] 安装 Pydantic...
    pip install pydantic -q
) else (
    echo [+] Pydantic 已安装
)

REM 检查并安装Requests
pip show requests >nul 2>&1
if errorlevel 1 (
    echo [*] 安装 Requests...
    pip install requests -q
) else (
    echo [+] Requests 已安装
)

REM 检查并安装PyYAML
pip show pyyaml >nul 2>&1
if errorlevel 1 (
    echo [*] 安装 PyYAML...
    pip install pyyaml -q
) else (
    echo [+] PyYAML 已安装
)

REM 检查并安装Pillow
pip show Pillow >nul 2>&1
if errorlevel 1 (
    echo [*] 安装 Pillow...
    pip install Pillow -q
) else (
    echo [+] Pillow 已安装
)

echo.
echo [+] 环境准备完成！

REM 选择启动模式
echo.
echo 请选择启动模式:
echo 1. 启动Web界面 ^(推荐^)
echo 2. 启动桌宠
echo 3. 同时启动Web和桌宠
echo.
set /p choice=请输入选项 [1-3]: 

if "!choice!"=="1" goto web
if "!choice!"=="2" goto pet
if "!choice!"=="3" goto both
echo 无效选项
pause
exit /b 1

:web
echo.
echo [*] 启动Web界面...
echo [*] 访问地址: http://localhost:8000
echo.
cd /d "%~dp0web"
python -m uvicorn main:app --host 0.0.0.0 --port 8000
pause
exit /b 0

:pet
echo.
echo [*] 启动桌宠...
echo.
cd /d "%~dp0"
python desktop_pet.py
pause
exit /b 0

:both
echo.
echo [*] 启动Web界面 ^(后台^)...
start "RedOps Web" cmd /c "cd /d "%~dp0web" && python -m uvicorn main:app --host 0.0.0.0 --port 8000"
timeout /t 2 /nobreak >nul
echo [*] 启动桌宠...
cd /d "%~dp0"
python desktop_pet.py
pause
exit /b 0
