@echo off
setlocal enabledelayedexpansion

echo.
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║         Modelling Mate - Update Deployment Script                ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.

:: Configuration - OneDrive Updates Folder (Shared Structure)
set "UPDATE_SERVER=C:\Users\CameronRoberts\OneDrive - im-sciences.com\MasterDrive\Dev\04 - Python Modelling Toolkit\ModelHub-Updates"

:: Get version from package.json
for /f "tokens=2 delims=:, " %%a in ('findstr /C:"version" ..\package.json') do (
    set VERSION=%%a
    set VERSION=!VERSION:"=!
)

echo Current Version: %VERSION%
echo Update Server: %UPDATE_SERVER%
echo.

:: Confirm deployment
echo This will deploy the following files:
echo   - Modelling Mate Setup %VERSION%.exe
echo   - latest.yml
echo.
set /p CONFIRM="Continue with deployment? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo Deployment cancelled.
    pause
    exit /b 0
)

echo.
echo [1/4] Building application...
cd ..
call npm run electron:build:win

if errorlevel 1 (
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo [2/4] Checking build output...
set "INSTALLER=dist\Modelling Mate Setup %VERSION%.exe"
set "METADATA=dist\latest.yml"

if not exist "%INSTALLER%" (
    echo [ERROR] Installer not found: %INSTALLER%
    pause
    exit /b 1
)

if not exist "%METADATA%" (
    echo [ERROR] Metadata not found: %METADATA%
    pause
    exit /b 1
)

echo ✓ Found installer: %INSTALLER%
echo ✓ Found metadata: %METADATA%

echo.
echo [3/4] Copying files to update server...

:: Check if update server is accessible
if "%UPDATE_SERVER:~0,2%"=="\\" (
    :: Network share
    if not exist "%UPDATE_SERVER%" (
        echo [ERROR] Cannot access update server: %UPDATE_SERVER%
        echo Please check:
        echo   1. Network connection
        echo   2. Share permissions
        echo   3. Share path is correct
        pause
        exit /b 1
    )

    echo Copying to network share...
    copy /Y "%INSTALLER%" "%UPDATE_SERVER%\" >nul
    copy /Y "%METADATA%" "%UPDATE_SERVER%\" >nul

    if errorlevel 1 (
        echo [ERROR] Failed to copy files
        echo Check write permissions on: %UPDATE_SERVER%
        pause
        exit /b 1
    )
) else (
    :: Web server - requires manual upload or additional tools
    echo [INFO] For web server deployment:
    echo   1. Upload these files to %UPDATE_SERVER%:
    echo      - %INSTALLER%
    echo      - %METADATA%
    echo   2. Press any key when upload is complete
    pause
)

echo.
echo [4/4] Verifying deployment...

:: Verify files exist on server (network share only)
if "%UPDATE_SERVER:~0,2%"=="\\" (
    if exist "%UPDATE_SERVER%\latest.yml" (
        echo ✓ Verified latest.yml on server
    ) else (
        echo [WARNING] Could not verify latest.yml
    )

    if exist "%UPDATE_SERVER%\Modelling Mate Setup %VERSION%.exe" (
        echo ✓ Verified installer on server
    ) else (
        echo [WARNING] Could not verify installer
    )
)

:: Create deployment log
set "LOG_FILE=scripts\deployment-log.txt"
echo ──────────────────────────────────────────── >> "%LOG_FILE%"
echo Deployment: %DATE% %TIME% >> "%LOG_FILE%"
echo Version: %VERSION% >> "%LOG_FILE%"
echo Server: %UPDATE_SERVER% >> "%LOG_FILE%"
echo User: %USERNAME% >> "%LOG_FILE%"
echo Status: SUCCESS >> "%LOG_FILE%"

echo.
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║                    Deployment Complete!                           ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.
echo Version %VERSION% has been deployed to:
echo   %UPDATE_SERVER%
echo.
echo All clients will receive the update within 4 hours.
echo Users can also manually check: Help → Check for Updates
echo.
echo Deployment logged to: %LOG_FILE%
echo.

pause
exit /b 0
