@echo off
REM ============================================================================
REM Build Python Backend with PyInstaller
REM This script creates a standalone executable bundle of the Python backend
REM ============================================================================

echo ========================================
echo Building Python Backend Bundle
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9-3.11 from python.org
    echo.
    pause
    exit /b 1
)

echo [1/5] Checking Python version...
python --version
echo.

REM Navigate to backend directory
cd /d "%~dp0\..\backend"

echo [2/5] Installing/upgrading dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    echo.
    pause
    exit /b 1
)
echo Dependencies installed successfully
echo.

echo [3/5] Cleaning previous build...
if exist "dist\modelling-mate-backend" (
    rmdir /s /q "dist\modelling-mate-backend"
    echo Removed old build directory
)
if exist "build" (
    rmdir /s /q "build"
    echo Removed build cache
)
echo.

echo [4/5] Building backend with PyInstaller...
echo This may take 5-10 minutes...
python -m PyInstaller main.spec --clean
if errorlevel 1 (
    echo ERROR: PyInstaller build failed
    echo.
    pause
    exit /b 1
)
echo.

echo [5/5] Verifying build...
if not exist "dist\modelling-mate-backend\modelling-mate-backend.exe" (
    echo ERROR: Backend executable not found after build
    echo Expected: dist\modelling-mate-backend\modelling-mate-backend.exe
    echo.
    pause
    exit /b 1
)

REM Get the size of the build
for %%A in ("dist\modelling-mate-backend") do set size=%%~zA
set /a size_mb=%size:~0,-6%
echo Build successful!
echo Location: %CD%\dist\modelling-mate-backend\
echo Size: ~%size_mb% MB
echo.

echo ========================================
echo Testing the bundled backend...
echo ========================================
echo Starting backend (will auto-stop after 10 seconds)...
echo.

REM Start the backend in background and test it
start /B dist\modelling-mate-backend\modelling-mate-backend.exe

REM Wait for backend to start
timeout /t 5 /nobreak >nul

REM Test health endpoint
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo WARNING: Backend may not be responding on port 8000
    echo This could be normal if port is already in use
    echo.
) else (
    echo SUCCESS: Backend is responding!
    echo.
)

REM Stop the test backend
taskkill /F /IM modelling-mate-backend.exe >nul 2>&1

echo ========================================
echo Build Complete!
echo ========================================
echo.
echo The bundled backend is ready at:
echo %CD%\dist\modelling-mate-backend\
echo.
echo Next steps:
echo 1. Run the Electron build: npm run electron:build:win
echo 2. The backend will be automatically included in the installer
echo.
pause
