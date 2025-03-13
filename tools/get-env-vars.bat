set env_file=devdata\env.json
if not exist !env_file! (
    set env_file=..\devdata\env.json
)

:: Read miniforge3 path from devdata\env.json
for /f "tokens=* delims=" %%a in ('findstr "MINIFORGE3_PATH" !env_file!') do (
    set "line=%%a"
)
:: Remove quotes, comma and spaces
set "line=!line:    =!"
set "line=!line:"=!"
set "line=!line:,=!"

:: Split the line at colon and take the second part
for /f "tokens=2 delims= " %%a in ("!line!") do (
    set MINIFORGE3_PATH=%%a
)

:: Read miniforge3 config file from devdata\env.json
for /f "tokens=* delims=" %%a in ('findstr "MINIFORGE3_CONFIG" !env_file!') do (
    set "line=%%a"
)
:: Remove quotes, comma and spaces
set "line=!line:    =!"
set "line=!line:"=!"
set "line=!line:,=!"

:: Split the line at colon and take the second part
for /f "tokens=2 delims= " %%a in ("!line!") do (
    set MINIFORGE3_CONFIG=%%a
)

:: Read task wait timeout from devdata\env.json
for /f "tokens=* delims=" %%a in ('findstr "TASK_WAIT_TIMEOUT" !env_file!') do (
    set "line=%%a"
)
:: Remove quotes, comma and spaces
set "line=!line:    =!"
set "line=!line:"=!"
set "line=!line:,=!"

:: Split the line at colon and take the second part
for /f "tokens=2 delims= " %%a in ("!line!") do (
    set TASK_WAIT_TIMEOUT=%%a
)
