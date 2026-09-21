@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo WireAtlas virtual environment was not found.
    echo.
    echo Create it with:
    echo     py -3.14 -m venv .venv
    echo.
    echo Then install the required packages with:
    echo     .venv\Scripts\python.exe -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m wireatlas.main

endlocal