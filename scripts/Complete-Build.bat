@echo off
REM ============================================================================
REM Complete Build Script for Modelling Mate with Bundled Python Backend
REM This script builds both the Python backend bundle and the Electron app
REM ============================================================================

echo.
echo ============================================================================
echo            Modelling Mate - Complete Build with Bundled Backend
echo ============================================================================
echo.
echo This will:
echo   1. Build Python backend with PyInstaller (~10 min)
echo   2. Build Next.js frontend (~2 min)
echo   3. Package Electron installer (~5 min)
echo.
echo Total estimated time: 15-20 minutes
echo.
pause

REM Store the root directory
set ROOT_DIR=%CD%\..

REM Step 1: Build Python backend
echo.
echo ============================================================================
echo [1/3] Building Python Backend Bundle
echo ============================================================================
echo.
cd "%ROOT_DIR%\scripts"
call build-python-backend.bat
if errorlevel 1 (
    echo.
    echo ERROR: Python backend build failed
    echo Please check the error messages above
    echo.
    pause
    exit /b 1
)

REM Step 2: Build Next.js frontend
echo.
echo ============================================================================
echo [2/3] Building Next.js Frontend
echo ============================================================================
echo.
cd "%ROOT_DIR%"
call npm run build
if errorlevel 1 (
    echo.
    echo ERROR: Next.js build failed
    echo Please check the error messages above
    echo.
    pause
    exit /b 1
)

REM Step 3: Build Electron installer
echo.
echo ============================================================================
echo [3/3] Building Electron Installer
echo ============================================================================
echo.
call npm run electron:build:win
if errorlevel 1 (
    echo.
    echo ERROR: Electron build failed
    echo Please check the error messages above
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo                        Build Complete!
echo ============================================================================
echo.

REM Find the installer
for %%F in ("%ROOT_DIR%\dist\Modelling Mate Setup*.exe") do (
    set INSTALLER=%%~nxF
    set INSTALLER_SIZE=%%~zF
)

if defined INSTALLER (
    set /a SIZE_MB=%INSTALLER_SIZE:~0,-6%
    echo Installer created successfully:
    echo   Name: %INSTALLER%
    echo   Location: %ROOT_DIR%\dist\
    echo   Size: ~%SIZE_MB% MB
) else (
    echo WARNING: Could not find installer in dist\ folder
    echo Please check: %ROOT_DIR%\dist\
)

echo.
echo Next steps:
echo   1. Test the installer on a clean machine (no Python installed)
echo   2. Distribute to users
echo   3. Users just install and run - no Python setup needed!
echo.
echo Technical details:
echo   - Bundled backend: backend\dist\modelling-mate-backend\
echo   - Next.js build: out\
echo   - Electron build: dist\win-unpacked\ (for testing)
echo.
pause
