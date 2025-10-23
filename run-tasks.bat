:: Run tasks from within working time tray icon menu
::
@echo off
setlocal EnableDelayedExpansion

:: Set up error log file and clear if exists
set ERROR_LOG=wdttc-errors.log
if exist "%ERROR_LOG%" del "%ERROR_LOG%" 2>nul

:: Detect if running without console window
set "HEADLESS_MODE=0"
if "%WDTTC_HEADLESS%"=="1" set "HEADLESS_MODE=1"

:: Read environment variables from devdata\env.json
call tools\get-env-vars.bat

:: If standalone exe exists, skip miniforge3 environment setup
if exist "wdttc.exe" (
    echo Using standalone executable
    set launcher=wdttc.exe
    set TASK_WAIT_TIMEOUT=0
    goto STANDALONE
) else (
    set launcher=python src/wdttc.py
)

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

:: If standalone exe exists, skip miniforge3 environment setup
:STANDALONE

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
  if "!MyChoice!" == "Setup" set valid=1
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

:: Icon
if "!MyChoice!"=="Icon" ( 
  !launcher! runtrayicon
  exit /b %errorlevel%
)
:: Language
if "!MyChoice!"=="Language" ( 
  !launcher! taskslocales
  pause
  exit /b %errorlevel%
)
:: Setup
if "!MyChoice!"=="Setup" ( 
:: open vault.json for editing
  notepad ".\devdata\!VAULT_FILE!"
    exit /b %errorlevel%
)

if !TASK_WAIT_TIMEOUT! neq 0 (
  echo .
  echo .
  echo The Check-!MyChoice! task will be executed in !TASK_WAIT_TIMEOUT! seconds. Press any key to continue.
  echo .
  timeout /t !TASK_WAIT_TIMEOUT!
)

:: run the task
::!launcher! tasks !MyChoice!
call :RunTaskWithErrorHandling "tasks" "!MyChoice!" "!MyChoice!" || exit /b !errorlevel!
exit /b 0

REM ============================================================================
REM Function: RunTaskWithErrorHandling
REM Parameters: 
REM   %1 = Module/command (e.g., "tasks", "plugins.teams_tasks")
REM   %2 = Task argument (e.g., "In", "Out", "Available")
REM   %3 = Display name for error messages
REM ============================================================================
:RunTaskWithErrorHandling
setlocal
set "MODULE=%~1"
set "TASK_ARG=%~2"
set "DISPLAY_NAME=%~3"

REM Execute the task and capture errors
!launcher! %MODULE% "%TASK_ARG%" 2>>"%ERROR_LOG%"
set "EXIT_CODE=!errorlevel!"

if !EXIT_CODE! neq 0 (
    if "!HEADLESS_MODE!"=="1" (
        powershell -WindowStyle Hidden -Command "& {Add-Type -AssemblyName System.Windows.Forms; $notify = New-Object System.Windows.Forms.NotifyIcon; $notify.Icon = [System.Drawing.SystemIcons]::Error; $notify.Visible = $true; $notify.BalloonTipIcon = [System.Windows.Forms.ToolTipIcon]::Error; $notify.BalloonTipTitle = '%DISPLAY_NAME% Error'; $notify.BalloonTipText = '%DISPLAY_NAME% task failed. Check log: %ERROR_LOG%'; $notify.ShowBalloonTip(10000); Start-Sleep -Seconds 10; $notify.Dispose()}"
    ) else (
        echo Error occurred during %DISPLAY_NAME% task. Check log: %ERROR_LOG%
        pause
    )
)

endlocal & exit /b %EXIT_CODE%