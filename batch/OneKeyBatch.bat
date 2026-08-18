@echo off
cd /D "%~dp0"
cd ..

call conda activate ai-video-subtitle

@rem 运行批处理脚本
call python batch\utils\batch_processor.py

:end
pause
