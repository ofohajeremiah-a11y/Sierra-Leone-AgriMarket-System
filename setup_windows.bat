@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo Sierra Leone AgriMarket Intelligence Platform - Windows Setup
echo ============================================================
echo.

where py >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found.
    echo Please install Python 3.11, 3.12, or 3.13 from https://www.python.org/downloads/windows/
    echo During installation, tick: Add python.exe to PATH
    pause
    exit /b 1
)

for /f "delims=" %%V in ('py --version 2^>^&1') do echo %%V

echo.
echo [1/5] Creating Python virtual environment...
if not exist ".venv\Scripts\python.exe" (
    py -m venv .venv
    if errorlevel 1 (
        echo ERROR: Could not create the virtual environment.
        pause
        exit /b 1
    )
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
    echo ERROR: Could not activate the virtual environment.
    pause
    exit /b 1
)

echo.
echo [2/5] Upgrading pip...
python -m pip install --upgrade pip --index-url https://pypi.org/simple
if errorlevel 1 (
    echo ERROR: pip could not be upgraded. Check your internet connection.
    pause
    exit /b 1
)

echo.
echo [3/5] Installing Python packages from official PyPI...
python -m pip install --only-binary=:all: -r backend\requirements.txt --index-url https://pypi.org/simple
if errorlevel 1 (
    echo.
    echo ============================================================
    echo INSTALLATION FAILED
    echo ============================================================
    echo The error above is the part we need to fix.
    echo Do NOT run start_backend.bat yet.
    pause
    exit /b 1
)

echo.
echo [4/5] Setting up the Django database...
cd backend
python manage.py migrate
if errorlevel 1 (
    echo ERROR: Django database migration failed.
    cd ..
    pause
    exit /b 1
)

python manage.py seed_demo
if errorlevel 1 (
    echo ERROR: Demo data setup failed.
    cd ..
    pause
    exit /b 1
)
cd ..

echo.
echo [5/5] Checking Django installation...
python -c "import django; print('Django version:', django.get_version())"
if errorlevel 1 (
    echo ERROR: Django is still not available.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo SUCCESS! AgriMarket backend setup is complete.
echo ============================================================
echo.
echo Next:
echo 1. Double-click start_backend.bat
echo 2. Double-click start_frontend.bat
echo 3. Open http://localhost:5173/
echo.
pause
