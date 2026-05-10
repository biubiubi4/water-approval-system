@echo off
echo ========================================
echo   涉水审批AI服务 - 环境设置脚本
echo ========================================
echo.

echo [1/4] 创建虚拟环境...
python -m venv venv
if %errorlevel% neq 0 (
    echo 错误：无法创建虚拟环境
    pause
    exit /b 1
)

echo [2/4] 激活虚拟环境...
call venv\Scripts\activate.bat

echo [3/4] 升级pip...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

echo [4/4] 安装依赖...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo   安装过程中出现问题，尝试单独安装
    echo ========================================
    pip install fastapi uvicorn python-multipart -i https://pypi.tuna.tsinghua.edu.cn/simple
)

echo.
echo ========================================
echo   安装完成！
echo ========================================
echo.
echo 启动AI服务请运行：
echo   venv\Scripts\activate
echo   python main.py
echo.
pause
