@echo off
echo Adding the current directory to the PATH...

:: Get the current directory
set CURRENT_DIR=%cd%

:: Get the current PATH from the registry
for /f "tokens=* delims=" %%A in ('reg query "HKCU\Environment" /v PATH 2^>nul') do (
    set "CURRENT_PATH=%%A"
)

:: Extract only the actual PATH value from the registry query result
for /f "tokens=2,* delims=    " %%A in ("%CURRENT_PATH%") do (
    set "CURRENT_PATH=%%B"
)

:: Check if the current directory is already in PATH
echo %CURRENT_PATH% | find "%CURRENT_DIR%" >nul
if %errorlevel% equ 0 (
    echo The current directory is already in PATH.
    goto :END
)

:: Append the current directory to the PATH
set NEW_PATH=%CURRENT_PATH%;%CURRENT_DIR%

:: Update the PATH in the registry
reg add "HKCU\Environment" /v PATH /t REG_SZ /d "%NEW_PATH%" /f

echo Successfully added %CURRENT_DIR% to PATH.

:END
echo Installation complete! You can now use the 'bb' command.
pause
