@echo off
chcp 65001 >nul 2>&1
call conda activate ai-video-subtitle 2>nul
set PYTHONWARNINGS=ignore
python "%~dp0launch.py"
if %errorlevel% neq 0 (
    echo.
    echo  Pre-flight checks or Streamlit failed. See logs\ for details.
    echo.
)
pause
