@echo off
cd /d %~dp0
start /min ollama serve
timeout /t 1
set "VENV_PYTHON=%~dp0.venv\Scripts\python.exe"
if not exist "%VENV_PYTHON%" (
    echo Virtual environment Python not found at: %VENV_PYTHON%
    pause
    exit /b 1
)
start http://localhost:5000
"%VENV_PYTHON%" app.py 