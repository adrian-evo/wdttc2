@echo off
setlocal EnableDelayedExpansion

:: Read environment variables from devdata\env-dev.json or env.json
call get-env-vars.bat

:: activate miniforge3 environment if available
if exist "!MINIFORGE3_PATH!/Scripts/activate.bat" (
    if exist "!MINIFORGE3_PATH!/envs/wdttc" (
        echo Using Miniforge3 wdttc environment
        call "!MINIFORGE3_PATH!/Scripts/activate" wdttc
    ) else (
        echo Miniforge3 wdttc environment not found. Please create it first.
        pause
        exit /b %errorlevel%
    )
)

:: Check Python is installed
python --version 2>nul
if %errorlevel% neq 0 (
    echo "Python is not installed. Please install Python first (miniforge3, choco, standalone), or adjust path in env.json"
    echo !MINIFORGE3_PATH!/Scripts/activate.bat
    pause
    exit /b %errorlevel%
)

if exist dist (
    echo Remove old dist folder
    rmdir /s /q dist
    mkdir dist
)

echo Check if pyinstaller is installed
python -W ignore -m pip.__main__ show pyinstaller | findstr Version
if !errorlevel! == 1 (
    echo pyinstaller is not installed. Will install it now...
    pause
    python -W ignore -m pip.__main__ install pyinstaller
    pause
)

pyinstaller wdttc.spec

copy ..\run-tasks.bat dist\wdttc
if exist ..\setup-wdttc.bat copy ..\setup-wdttc.bat dist\wdttc
mkdir dist\wdttc\locales
xcopy /s /i ..\locales dist\wdttc\locales
mkdir dist\wdttc\devdata
copy ..\devdata\env.json dist\wdttc\devdata
copy ..\devdata\!VAULT_FILE:.json=-rel.json! dist\wdttc\devdata\!VAULT_FILE!
mkdir dist\wdttc\tools
copy get-env-vars.bat dist\wdttc\tools

echo Create standalone-wdttc.zip package
powershell -Command "& {Compress-Archive -Force -Path "dist\*" -DestinationPath "dist\standalone-wdttc.zip";}"

pause