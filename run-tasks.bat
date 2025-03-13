:: Run tasks from within working time tray icon menu
::
@echo off
setlocal EnableDelayedExpansion

:: Read environment variables from devdata\env.json
call tools\get-env-vars.bat

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
    echo "Python is not installed. Please install Python first (miniforge3, choco, standalone)."
    echo !MINIFORGE3_PATH!/Scripts/activate.bat
    pause
    exit /b %errorlevel%
)

:: If run without arguments, ask it
:ASK
set "MyChoice=%~1"

if "!MyChoice!"=="" ( 
  set MyChoice=Icon
  set /p MyChoice="Type the task to execute: In, Out, Verify, Custom, Icon [!MyChoice!]: "
  :: Check the choice is valid
  if "!MyChoice!" == "In" set valid=1
  if "!MyChoice!" == "Out" set valid=1
  if "!MyChoice!" == "Verify" set valid=1
  if "!MyChoice!" == "Custom" set valid=1
  if "!MyChoice!" == "Icon" set valid=1
  if "!MyChoice!" == "Startup" set valid=1
  if "!MyChoice!" == "Language" set valid=1
  if not defined valid (
    echo The !MyChoice! is invalid task. Please choose a valid task or close window to exit.
    goto ASK
  )
)

:: Startup choice will add or remove a shortcut to Windows Startup folder, that will automatically restart the Icon after computer restart
if "!MyChoice!" == "Startup" (
  if exist "%userprofile%\Start Menu\Programs\Startup\%~n0.lnk" (
    echo The file %userprofile%\Start Menu\Programs\Startup\%~n0.lnk will be deleted now.
    pause
    del "%userprofile%\Start Menu\Programs\Startup\%~n0.lnk"
  ) else (
    echo The file %userprofile%\Start Menu\Programs\Startup\%~n0.lnk will be created and will be executed at computer restart.
    pause
    powershell "$s=(New-Object -COM WScript.Shell).CreateShortcut('%userprofile%\Start Menu\Programs\Startup\%~n0.lnk');$s.TargetPath='%~f0';$s.WorkingDirectory='%~dp0';$s.Arguments='Icon';$s.Save()"
  )
  exit /b %errorlevel%
)

echo .
echo .
echo The Check-!MyChoice! task will be executed in !TASK_WAIT_TIMEOUT! seconds. Press any key to continue.
echo .
timeout /t !TASK_WAIT_TIMEOUT!

:: Icon
if "!MyChoice!"=="Icon" ( 
  python src/runtrayicon.py
  exit /b %errorlevel%
)
:: Language
if "!MyChoice!"=="Language" ( 
  python src/taskslocales.py
  pause
  exit /b %errorlevel%
)

:: run the task
python src/tasks.py !MyChoice!
