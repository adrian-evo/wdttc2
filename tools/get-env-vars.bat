
:: Set env_file to the first available file in order
if exist devdata\env-dev.json (
    set env_file=devdata\env-dev.json
) else if exist ..\devdata\env-dev.json (
    set env_file=..\devdata\env-dev.json
) else if exist devdata\env.json (
    set env_file=devdata\env.json
) else if exist ..\devdata\env.json (
    set env_file=..\devdata\env.json
)


:: Read vault file name from devdata\env.json
for /f "tokens=* delims=" %%a in ('findstr "VAULT_FILE" !env_file!') do (
    set "line=%%a"
)
:: Remove quotes, comma and spaces
set "line=!line:    =!"
set "line=!line:"=!"
set "line=!line:,=!"

:: Split the line at colon and take the second part
for /f "tokens=2 delims= " %%a in ("!line!") do (
    set VAULT_FILE=%%a
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
