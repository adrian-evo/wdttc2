:: This batch file will create and install:
:: 		- conda wdttc environment
::		- python modules

@echo off
setlocal EnableDelayedExpansion

:: Read environment variables from devdata\env-dev.json or env.json
call get-env-vars.bat

:: activate miniforge3 environment if available
echo Searching for !MINIFORGE3_PATH!
if not exist "!MINIFORGE3_PATH!/Scripts/activate.bat" (
    echo .
    echo Miniforge3 not found. Please install it first!
    pause
    exit
)
call "!MINIFORGE3_PATH!/Scripts/activate"

if exist "!MINIFORGE3_PATH!/envs/wdttc" (
    echo .
    echo This will cleanup the existing Miniforge3 wdttc environment. Close window to cancel.
    echo .
    pause
    call conda env remove -n wdttc --yes
) 

echo .
echo Creating Miniforge3 wdttc environment from plugins/miniforge.yml file. Close window to cancel.
echo .
pause

call conda env create -f ../plugins/miniforge.yml
call conda env list
call conda activate wdttc
pip list
echo .
echo Miniforge3 wdttc environment was created and activated, and contains the above Python modules.
echo .
echo Installing Playwright chromium browser. Close window to cancel.
echo .
pause
call playwright install chromium
echo .
pause
