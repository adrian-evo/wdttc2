@echo off
setlocal EnableDelayedExpansion

:: Change to parent directory (project root)
cd /D %~dp0\..

:: Read environment variables from devdata\env-dev.json or env.json
call tools\get-env-vars.bat

:: activate uv environment if available
if exist ".venv\Scripts\activate.bat" (
    echo Using uv virtual environment
    call .venv\Scripts\activate
) else (
    echo uv virtual environment not found. Please create it first.
    pause
    exit /b %errorlevel%
)

:: Check Python is installed
python --version 2>nul
if %errorlevel% neq 0 (
    echo "Python is not installed in the virtual environment."
    pause
    exit /b %errorlevel%
)

if exist dist (
    echo Remove old dist folder
    rmdir /s /q dist
    mkdir dist
)

echo Check if pyinstaller is installed
uv pip show pyinstaller >nul 2>&1
if !errorlevel! neq 0 (
    echo pyinstaller is not installed. Will install it now...
    uv pip install pyinstaller
    if !errorlevel! neq 0 (
        echo Failed to install pyinstaller
        pause
        exit /b !errorlevel!
    )
    echo pyinstaller installed successfully
)

cd tools
pyinstaller wdttc.spec
cd ..

copy run-tasks.bat tools\dist\wdttc
if exist setup-wdttc.bat copy setup-wdttc.bat tools\dist\wdttc
mkdir tools\dist\wdttc\locales
xcopy /s /i locales tools\dist\wdttc\locales
mkdir tools\dist\wdttc\devdata
copy devdata\env.json tools\dist\wdttc\devdata
copy devdata\!VAULT_FILE:.json=-rel.json! tools\dist\wdttc\devdata\!VAULT_FILE!
mkdir tools\dist\wdttc\tools
copy tools\get-env-vars.bat tools\dist\wdttc\tools

echo Create standalone-wdttc.zip package
powershell -Command "& {Compress-Archive -Force -Path "tools\dist\*" -DestinationPath "tools\dist\standalone-wdttc.zip";}"

pause