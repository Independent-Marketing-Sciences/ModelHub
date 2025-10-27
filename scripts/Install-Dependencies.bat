@echo off
setlocal enabledelayedexpansion

:: Set UTF-8 encoding for proper character display
chcp 65001 >nul 2>&1

echo.
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║         Modelling Mate - Python Dependencies Installer            ║
echo ║                      Version 1.0                                  ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.

:: Color support (optional - works on Windows 10+)
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "NC=[0m"

:: ============================================================================
:: STEP 1: Check for Python Installation
:: ============================================================================
echo [1/5] Checking Python installation...
echo.

:: Try multiple common Python commands
set "PYTHON_CMD="
for %%p in (python python3 py) do (
    %%p --version >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_CMD=%%p"
        goto :python_found
    )
)

:python_not_found
echo %RED%[ERROR] Python is not installed or not in PATH%NC%
echo.
echo Python is required to run Modelling Mate's analytics features.
echo.
echo Options to fix this:
echo.
echo Option 1 - Install Python (Recommended):
echo   1. Go to: https://www.python.org/downloads/
echo   2. Download Python 3.8 or later (3.9+ recommended)
echo   3. Run installer and CHECK "Add Python to PATH"
echo   4. Restart this installer
echo.
echo Option 2 - Use existing Python:
echo   If Python is already installed but not in PATH:
echo   1. Search for "Environment Variables" in Windows
echo   2. Add Python folder to your PATH
echo   3. Restart this installer
echo.
pause
exit /b 1

:python_found
echo %GREEN%[✓]%NC% Python found: %PYTHON_CMD%
%PYTHON_CMD% --version
echo.

:: Check Python version
for /f "tokens=2" %%v in ('%PYTHON_CMD% --version 2^>^&1') do set PYTHON_VERSION=%%v
echo Python version: %PYTHON_VERSION%

:: Note: Prophet 1.1.7 supports Python 3.8-3.12

:: ============================================================================
:: STEP 2: Locate Installation Directory
:: ============================================================================
echo [2/5] Locating Modelling Mate installation...
echo.

:: Try multiple possible installation locations
set "BACKEND_PATH="

:: Location 1: Standard user install
set "TEST_PATH=%LOCALAPPDATA%\Programs\modelling-mate\resources\app.asar.unpacked\backend"
if exist "%TEST_PATH%" (
    set "BACKEND_PATH=%TEST_PATH%"
    goto :backend_found
)

:: Location 2: System-wide install
set "TEST_PATH=%ProgramFiles%\Modelling Mate\resources\app.asar.unpacked\backend"
if exist "%TEST_PATH%" (
    set "BACKEND_PATH=%TEST_PATH%"
    goto :backend_found
)

:: Location 3: Current directory (for portable/dev versions)
set "TEST_PATH=%~dp0..\backend"
if exist "%TEST_PATH%" (
    set "BACKEND_PATH=%TEST_PATH%"
    goto :backend_found
)

:: Location 4: Ask user to specify
echo %YELLOW%[!] Could not auto-detect installation location%NC%
echo.
echo Please enter the path to Modelling Mate installation:
echo (Example: C:\Users\YourName\AppData\Local\Programs\modelling-mate)
echo.
set /p "USER_PATH=Installation path: "
set "TEST_PATH=%USER_PATH%\resources\app.asar.unpacked\backend"
if exist "%TEST_PATH%" (
    set "BACKEND_PATH=%TEST_PATH%"
    goto :backend_found
)

echo %RED%[ERROR] Cannot find Modelling Mate installation%NC%
echo.
echo Please make sure Modelling Mate is installed first.
echo Searched locations:
echo   - %LOCALAPPDATA%\Programs\modelling-mate\
echo   - %ProgramFiles%\Modelling Mate\
echo.
pause
exit /b 1

:backend_found
echo %GREEN%[✓]%NC% Found installation at:
echo     %BACKEND_PATH%
echo.

:: Check for requirements.txt
if not exist "%BACKEND_PATH%\requirements.txt" (
    echo %RED%[ERROR] requirements.txt not found in backend folder%NC%
    echo This installation may be corrupted.
    echo.
    pause
    exit /b 1
)

cd /d "%BACKEND_PATH%"

:: ============================================================================
:: STEP 3: Upgrade pip
:: ============================================================================
echo [3/5] Upgrading pip...
echo.

%PYTHON_CMD% -m pip install --upgrade pip --quiet
if !errorlevel! neq 0 (
    echo %YELLOW%[WARNING] Could not upgrade pip, continuing with current version...%NC%
) else (
    echo %GREEN%[✓]%NC% pip upgraded successfully
)
echo.

:: ============================================================================
:: STEP 4: Install Dependencies (excluding Prophet)
:: ============================================================================
echo [4/5] Installing core dependencies...
echo.
echo This may take 3-5 minutes. Please wait...
echo.

:: Create a temporary requirements file without Prophet
type requirements.txt | findstr /v "prophet" > requirements_temp.txt

%PYTHON_CMD% -m pip install -r requirements_temp.txt --no-warn-script-location

if !errorlevel! neq 0 (
    echo %RED%[ERROR] Failed to install core dependencies%NC%
    echo.
    echo This could be due to:
    echo   - Network connectivity issues
    echo   - Insufficient permissions
    echo   - Corrupted pip cache
    echo.
    echo Try running Command Prompt as Administrator and retry.
    echo.
    del requirements_temp.txt
    pause
    exit /b 1
)

echo %GREEN%[✓]%NC% Core dependencies installed successfully
echo.

del requirements_temp.txt

:: ============================================================================
:: STEP 5: Install Prophet (with fallback strategies)
:: ============================================================================
echo [5/5] Installing Prophet (advanced analytics)...
echo.

:: Prophet is complex - it needs C++ compiler on Windows
:: We'll try multiple installation strategies

echo Strategy 1: Standard pip install...
%PYTHON_CMD% -m pip install prophet==1.1.7 --no-warn-script-location --quiet

if !errorlevel! equ 0 (
    echo %GREEN%[✓]%NC% Prophet installed successfully!
    goto :test_prophet
)

echo %YELLOW%[!] Standard installation failed, trying alternative methods...%NC%
echo.

:: Strategy 2: Try installing pre-built wheel
echo Strategy 2: Attempting to install pre-compiled Prophet...
%PYTHON_CMD% -m pip install prophet==1.1.7 --prefer-binary --no-warn-script-location --quiet

if !errorlevel! equ 0 (
    echo %GREEN%[✓]%NC% Prophet installed using pre-compiled package!
    goto :test_prophet
)

:: Strategy 3: Install dependencies separately
echo Strategy 3: Installing Prophet dependencies separately...
%PYTHON_CMD% -m pip install pystan==2.19.1.1 --quiet
%PYTHON_CMD% -m pip install prophet==1.1.7 --no-warn-script-location --quiet

if !errorlevel! equ 0 (
    echo %GREEN%[✓]%NC% Prophet installed via dependency-first method!
    goto :test_prophet
)

:: Strategy 4: Try conda if available
where conda >nul 2>&1
if !errorlevel! equ 0 (
    echo Strategy 4: Attempting conda installation...
    conda install -c conda-forge prophet -y
    if !errorlevel! equ 0 (
        echo %GREEN%[✓]%NC% Prophet installed via conda!
        goto :test_prophet
    )
)

:: All strategies failed
echo.
echo %RED%[ERROR] Prophet installation failed%NC%
echo.
echo Prophet requires Microsoft C++ Build Tools to compile.
echo.
echo To install Prophet:
echo   1. Download Microsoft C++ Build Tools:
echo      https://visualstudio.microsoft.com/visual-cpp-build-tools/
echo   2. Run installer and select "Desktop development with C++"
echo   3. After installation completes, run this script again
echo.
echo %YELLOW%Note: The app will still work without Prophet%NC%
echo       Only the "Prophet Seasonality" tab will be unavailable.
echo.
echo Other analytics features (Correlation, Feature Extraction, etc.) work fine!
echo.

set "PROPHET_AVAILABLE=false"
goto :complete

:test_prophet
:: Verify Prophet actually works
echo.
echo Verifying Prophet installation...
%PYTHON_CMD% -c "import prophet; print('Prophet version:', prophet.__version__)" 2>&1

if !errorlevel! equ 0 (
    echo %GREEN%[✓]%NC% Prophet is working correctly!
    set "PROPHET_AVAILABLE=true"
) else (
    echo %YELLOW%[!]%NC% Prophet installed but not loading correctly
    set "PROPHET_AVAILABLE=false"
)

:complete
:: ============================================================================
:: Installation Complete
:: ============================================================================
echo.
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║                    Installation Complete!                         ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.
echo Summary:
echo   - Core dependencies: %GREEN%Installed%NC%
if "%PROPHET_AVAILABLE%"=="true" (
    echo   - Prophet ^(seasonality^): %GREEN%Available%NC%
) else (
    echo   - Prophet ^(seasonality^): %YELLOW%Not Available%NC%
)
echo.
echo You can now launch Modelling Mate from:
echo   - Start Menu
echo   - Desktop shortcut (if created)
echo.
echo If you encounter any issues:
echo   1. Check the backend logs in Modelling Mate
echo   2. Try running this installer as Administrator
echo   3. Contact support with the log file
echo.

:: Create a log file for troubleshooting
echo Installation Log > "%USERPROFILE%\ModellingMate_Install.log"
echo Date: %DATE% %TIME% >> "%USERPROFILE%\ModellingMate_Install.log"
echo Python: %PYTHON_CMD% >> "%USERPROFILE%\ModellingMate_Install.log"
%PYTHON_CMD% --version >> "%USERPROFILE%\ModellingMate_Install.log" 2>&1
echo Prophet: %PROPHET_AVAILABLE% >> "%USERPROFILE%\ModellingMate_Install.log"
echo Backend: %BACKEND_PATH% >> "%USERPROFILE%\ModellingMate_Install.log"

echo Log file created at: %USERPROFILE%\ModellingMate_Install.log
echo.

pause
exit /b 0
