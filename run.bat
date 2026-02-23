@echo off
setlocal

cd /d "%~dp0"

set "VENV_PY=venv\Scripts\python.exe"
set "PIP_EXE=venv\Scripts\pip.exe"

if /I "%~1"=="help" goto :help
if /I "%~1"=="setup" goto :setup
if /I "%~1"=="init-db" goto :initdb
if /I "%~1"=="prod" goto :prod
if /I "%~1"=="run" goto :run
if "%~1"=="" goto :run

echo Unknown command: %~1
echo.
goto :help

:check_python
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python not found in PATH. Install Python 3.10+ and retry.
    exit /b 1
)
exit /b 0

:ensure_venv
if exist "%VENV_PY%" exit /b 0
call :check_python
if errorlevel 1 exit /b 1
echo [INFO] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment.
    exit /b 1
)
exit /b 0

:setup
call :ensure_venv
if errorlevel 1 exit /b 1
echo [INFO] Installing dependencies...
"%PIP_EXE%" install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Dependency installation failed.
    exit /b 1
)
echo [INFO] Initializing database...
"%VENV_PY%" src\main.py --init-db
if errorlevel 1 (
    echo [ERROR] Database initialization failed.
    exit /b 1
)
echo [OK] Setup complete.
exit /b 0

:initdb
call :ensure_venv
if errorlevel 1 exit /b 1
echo [INFO] Initializing database...
"%VENV_PY%" src\main.py --init-db
if errorlevel 1 (
    echo [ERROR] Database initialization failed.
    exit /b 1
)
echo [OK] Database initialized.
exit /b 0

:run
call :ensure_venv
if errorlevel 1 exit /b 1
echo [INFO] Starting app in debug mode on http://127.0.0.1:5000
"%VENV_PY%" src\main.py --debug --host 127.0.0.1 --port 5000
exit /b %errorlevel%

:prod
call :ensure_venv
if errorlevel 1 exit /b 1
echo [INFO] Starting app in production mode on http://0.0.0.0:5000
"%VENV_PY%" src\main.py --host 0.0.0.0 --port 5000
exit /b %errorlevel%

:help
echo ML CTF Challenge launcher
echo.
echo Usage:
echo   run.bat setup      ^(create venv, install requirements, init DB^)
echo   run.bat init-db    ^(initialize DB only^)
echo   run.bat run        ^(start dev server, default^)
echo   run.bat prod       ^(start production-mode server^)
echo   run.bat help
echo.
echo Examples:
echo   run.bat setup
echo   run.bat run
exit /b 0
