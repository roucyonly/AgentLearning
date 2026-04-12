@echo off
echo ====================================
echo Teacher Avatar System - Quick Start
echo ====================================
echo.

cd /d "%~dp0"

echo [1/3] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    pause
    exit /b 1
)

echo [2/3] Installing core dependencies...
echo This may take a few minutes...
pip install fastapi uvicorn sqlalchemy pydantic pydantic-settings python-jose passlib python-multipart python-dotenv >nul 2>&1
pip install langchain langchain-openai langchain-core langchain-community >nul 2>&1
pip install bcrypt email-validator >nul 2>&1
if errorlevel 1 (
    echo WARNING: Some dependencies failed to install
) else (
    echo OK: Core dependencies installed
)

echo.
echo [3/3] Starting FastAPI server...
echo.
echo ====================================
echo Server will start at:
echo   http://localhost:8000
echo   http://localhost:8000/docs (API Docs)
echo ====================================
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn main:app --reload --host 0.0.0.0 --port 8000
