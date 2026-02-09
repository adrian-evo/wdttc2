REM filepath: tools/setup-uv-env.bat
@echo off
setlocal EnableDelayedExpansion

call get-env-vars.bat

echo Checking for uv installation...
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo uv not found. Installing uv...
    powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"
    if %errorlevel% neq 0 (
        echo Failed to install uv. Please install manually from https://github.com/astral-sh/uv
        pause
        exit /b 1
    )
)

cd /D %~dp0\..

if exist ".venv" (
    echo Removing existing .venv environment...
    rmdir /S /Q .venv
)

echo Creating uv virtual environment...
uv venv

echo Installing dependencies...
uv pip install -e .
uv run playwright install chromium

echo uv environment setup complete!
pause