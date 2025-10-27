@echo off
echo.
echo ═══════════════════════════════════════════════════════════
echo  Creating Modelling Mate Distribution Package
echo ═══════════════════════════════════════════════════════════
echo.

:: Get version from package.json
for /f "tokens=2 delims=:, " %%a in ('findstr /C:"version" ..\package.json') do (
    set VERSION=%%a
    set VERSION=!VERSION:"=!
)

echo Version: %VERSION%
echo.

:: Set paths
set "DIST_FOLDER=..\Modelling_Mate_Distribution"
set "INSTALLER_PATH=..\dist\Modelling Mate Setup %VERSION%.exe"

:: Check if installer exists
if not exist "%INSTALLER_PATH%" (
    echo [ERROR] Installer not found: %INSTALLER_PATH%
    echo.
    echo Please build the app first:
    echo   npm run electron:build:win
    echo.
    pause
    exit /b 1
)

:: Create distribution folder
echo [1/4] Creating distribution folder...
if exist "%DIST_FOLDER%" rmdir /s /q "%DIST_FOLDER%"
mkdir "%DIST_FOLDER%"

:: Copy installer
echo [2/4] Copying installer...
copy "%INSTALLER_PATH%" "%DIST_FOLDER%\" >nul

:: Copy dependency installer
echo [3/4] Copying Install-Dependencies.bat...
copy "Install-Dependencies.bat" "%DIST_FOLDER%\" >nul

:: Copy README from scripts folder
copy "README.txt" "%DIST_FOLDER%\README.txt" >nul

:: Create installation guide
echo [4/4] Creating installation guide...

(
echo ═══════════════════════════════════════════════════════════
echo  Modelling Mate - Installation Guide
echo ═══════════════════════════════════════════════════════════
echo.
echo QUICK START
echo ═══════════
echo.
echo 1. Install Python 3.11 from: https://www.python.org/downloads/
echo    IMPORTANT: Check "Add Python to PATH" during installation
echo.
echo 2. Run: Modelling Mate Setup %VERSION%.exe
echo    - Follow the wizard
echo    - Check "Install Python Dependencies" on finish page
echo.
echo 3. Wait 10-15 minutes for dependencies to install
echo.
echo 4. Launch from Start Menu or Desktop
echo.
echo.
echo REQUIREMENTS
echo ════════════
echo.
echo - Windows 10/11 (64-bit^)
echo - Python 3.9, 3.10, or 3.11 (NOT 3.12+^)
echo - 4GB RAM (8GB recommended^)
echo - 3GB disk space
echo.
echo.
echo TROUBLESHOOTING
echo ═══════════════
echo.
echo "Python backend failed to start"
echo   → Run Install-Dependencies.bat
echo   → Or: Menu -^> Tools -^> Install Python Dependencies
echo.
echo "Prophet installation failed"
echo   → Install C++ Build Tools:
echo     https://visualstudio.microsoft.com/visual-cpp-build-tools/
echo   → Select "Desktop development with C++"
echo   → Or continue without Prophet (forecasting unavailable^)
echo.
echo Installation log location:
echo   C:\Users\[YourName]\ModellingMate_Install.log
echo.
echo.
echo FEATURES
echo ════════
echo.
echo ✓ Data View - Import and explore Excel/CSV files
echo ✓ Charting - Visualize with transformations
echo ✓ Correlation - Variable relationship analysis
echo ✓ Outlier Detection - Find anomalies
echo ✓ Feature Extraction - Time series features
echo ✓ Prophet Seasonality - Forecasting (requires C++ tools^)
echo.
echo.
echo SUPPORT
echo ═══════
echo.
echo Email: support@im-sciences.com
echo Documentation: See README.txt in installation folder
echo.
echo ═══════════════════════════════════════════════════════════
echo IM Sciences Ltd © 2025
echo ═══════════════════════════════════════════════════════════
) > "%DIST_FOLDER%\INSTALLATION-GUIDE.txt"

echo.
echo ═══════════════════════════════════════════════════════════
echo  Distribution Package Created!
echo ═══════════════════════════════════════════════════════════
echo.
echo Location: %DIST_FOLDER%
echo.
echo Contents:
dir /b "%DIST_FOLDER%"
echo.
echo You can now:
echo 1. Zip this folder
echo 2. Share with users
echo 3. Or deploy via network/Group Policy
echo.

:: Ask to open folder
set /p OPEN="Open distribution folder? (Y/N): "
if /i "%OPEN%"=="Y" (
    explorer "%DIST_FOLDER%"
)

pause
