@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo  InteractiveCatalog - Windows build script
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found.
    echo Install Python from https://www.python.org/downloads/
    echo and tick "Add Python to PATH" during setup, then run this file again.
    pause
    exit /b 1
)

if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Building...
pyinstaller --noconfirm --clean interactive_catalog.spec
if errorlevel 1 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  Done. Your app is:
echo    dist\InteractiveCatalog\InteractiveCatalog.exe
echo
echo  Keep the whole "InteractiveCatalog" folder together and
echo  double-click the .exe to start (no dependencies needed).
echo ============================================
pause