@echo off
echo.
echo ═══════════════════════════════════════════════════════════
echo  Modelling Mate - Update Server Setup
echo ═══════════════════════════════════════════════════════════
echo.
echo This script will help you set up your update server.
echo.
pause

:choose_method
echo.
echo Choose update server type:
echo.
echo 1. Network Share (Recommended for company deployment)
echo 2. Local Folder (For testing only)
echo 3. Exit
echo.
set /p CHOICE="Enter choice (1-3): "

if "%CHOICE%"=="1" goto network_share
if "%CHOICE%"=="2" goto local_folder
if "%CHOICE%"=="3" exit /b 0
goto choose_method

:network_share
echo.
echo ─────────────────────────────────────────────────────────
echo Network Share Setup
echo ─────────────────────────────────────────────────────────
echo.
echo Enter your network share path.
echo Example: \\fileserver\shares\modelling-mate-updates
echo.
set /p SHARE_PATH="Share path: "

echo.
echo Testing access to: %SHARE_PATH%
dir "%SHARE_PATH%" >nul 2>&1

if errorlevel 1 (
    echo.
    echo [ERROR] Cannot access %SHARE_PATH%
    echo.
    echo Make sure:
    echo 1. The share exists
    echo 2. You have write permissions
    echo 3. Path is correct
    echo.
    set /p RETRY="Try again? (Y/N): "
    if /i "%RETRY%"=="Y" goto network_share
    goto choose_method
)

echo [✓] Share accessible
echo.
goto configure_app

:local_folder
echo.
echo ─────────────────────────────────────────────────────────
echo Local Folder Setup (Testing Only)
echo ─────────────────────────────────────────────────────────
echo.
echo WARNING: This is for TESTING only!
echo For real deployment, use a network share.
echo.
set /p CONFIRM="Continue with local folder? (Y/N): "
if /i not "%CONFIRM%"=="Y" goto choose_method

set "SHARE_PATH=C:\test-updates"
if not exist "%SHARE_PATH%" mkdir "%SHARE_PATH%"
echo Created: %SHARE_PATH%
echo.
goto configure_app

:configure_app
echo.
echo ─────────────────────────────────────────────────────────
echo Configuring Application
echo ─────────────────────────────────────────────────────────
echo.

:: Convert path for electron-builder.yml
:: Network: \\server\share → file://\\\\server\\share
:: Local: C:\path → file://C:/path

set "CONFIG_PATH=%SHARE_PATH%"

:: Check if network path
echo %SHARE_PATH% | findstr /r "^\\\\" >nul
if !errorlevel! equ 0 (
    :: Network path - needs file://\\\\ prefix
    set "CONFIG_PATH=file://\\%SHARE_PATH:\=\\%"
) else (
    :: Local path - needs file:// and forward slashes
    set "CONFIG_PATH=file://%SHARE_PATH:\=/%"
)

echo Update server will be: %CONFIG_PATH%
echo.

:: Update electron-builder.yml
cd ..
set "BUILDER_FILE=electron-builder.yml"

echo Updating %BUILDER_FILE%...

:: Create backup
copy "%BUILDER_FILE%" "%BUILDER_FILE%.backup" >nul

:: Update the URL in electron-builder.yml
powershell -Command "(Get-Content '%BUILDER_FILE%') -replace 'url: \"file://.*\"', 'url: \"%CONFIG_PATH%\"' | Set-Content '%BUILDER_FILE%'"

echo [✓] Configuration updated
echo Backup saved as: %BUILDER_FILE%.backup
echo.

:: Show what was changed
echo The following line was updated in electron-builder.yml:
powershell -Command "Select-String -Path '%BUILDER_FILE%' -Pattern 'url:' | Select-Object -First 1 | ForEach-Object { $_.Line }"
echo.

:rebuild
echo.
echo ─────────────────────────────────────────────────────────
echo Next Steps
echo ─────────────────────────────────────────────────────────
echo.
echo 1. Review electron-builder.yml to confirm the URL is correct
echo 2. Rebuild the app: npm run electron:build:win
echo 3. Deploy to all users (this version will check for updates)
echo.
echo After that, use scripts\deploy-update.bat to push updates!
echo.

set /p REBUILD="Build now? (Y/N): "
if /i "%REBUILD%"=="Y" (
    echo.
    echo Building application...
    call npm run electron:build:win

    echo.
    echo Build complete!
    echo Installer location: dist\Modelling Mate Setup [version].exe
    echo.
)

echo.
echo ═══════════════════════════════════════════════════════════
echo Setup Complete!
echo ═══════════════════════════════════════════════════════════
echo.
echo Update server: %SHARE_PATH%
echo Configuration: %CONFIG_PATH%
echo.
echo To deploy updates in the future:
echo   cd scripts
echo   deploy-update.bat
echo.

pause
exit /b 0
