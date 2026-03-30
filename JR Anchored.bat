@echo off
rem Double-click this file to launch JR Anchored.
rem It opens the graphical interface in your default browser.
rem
rem Requirements: Git for Windows must be installed (https://git-scm.com/download/win).

set "SCRIPT_DIR=%~dp0"
set "BASH=C:\Program Files\Git\bin\bash.exe"

if not exist "%BASH%" (
    echo.
    echo  Git for Windows was not found at the expected location:
    echo  %BASH%
    echo.
    echo  Please install Git for Windows from https://git-scm.com/download/win
    echo  and try again.
    echo.
    pause
    exit /b 1
)

"%BASH%" "%SCRIPT_DIR%bin/jr_app"
