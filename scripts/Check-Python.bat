@echo off
:: Silent Python checker - exits with code 0 if Python is available, 1 if not
:: Can be used by the main app to check prerequisites

:: Try to find Python
for %%p in (python python3 py) do (
    %%p --version >nul 2>&1
    if !errorlevel! equ 0 (
        exit /b 0
    )
)

:: Python not found
exit /b 1
