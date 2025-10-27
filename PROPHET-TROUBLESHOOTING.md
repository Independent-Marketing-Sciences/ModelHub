# Prophet Troubleshooting Guide

This guide helps resolve common issues with the Prophet Seasonality Analysis feature in ModelHub.

## Common Error Messages and Solutions

### 1. "Failed to fetch" Error

**Symptoms:**
- Error message: "Failed to fetch"
- Technical details show: "Error: Failed to fetch"

**Cause:**
The Python backend is not running or cannot be reached.

**Solutions:**

#### Solution A: Restart the Application
1. Close ModelHub completely
2. Relaunch ModelHub
3. Wait 10-15 seconds for the Python backend to start
4. Try running Prophet again

#### Solution B: Verify Python Installation
1. Open Command Prompt
2. Run: `python --version`
3. You should see Python 3.8 or higher
4. If not installed, download from https://www.python.org/downloads/

#### Solution C: Install/Reinstall Dependencies
1. Locate the ModelHub installation folder:
   - Default: `C:\Users\[YourUsername]\AppData\Local\Programs\modelling-mate\`
2. Find `Install-Dependencies.bat` in the installation folder
3. Right-click and select "Run as Administrator"
4. Wait for installation to complete (5-10 minutes)
5. Restart ModelHub

### 2. "Prophet not being installed"

**Symptoms:**
- Error mentions Prophet library not found
- Backend reports `prophet_available: false`

**Cause:**
Prophet library is not installed in your Python environment.

**Solutions:**

#### Manual Installation:
1. Open Command Prompt as Administrator
2. Run: `pip install prophet==1.1.7`
3. Wait for installation (may take 5-10 minutes on first install)
4. If you see errors about C++ Build Tools:
   - Download Visual Studio Build Tools: https://visualstudio.microsoft.com/downloads/
   - Install "Desktop development with C++" workload
   - Retry Prophet installation
5. Restart ModelHub

### 3. "'Prophet' object has no attribute 'stan_backend'"

**Symptoms:**
- Error mentions `stan_backend`
- Occurs when trying to generate forecast

**Cause:**
Prophet version is outdated or incompatible with your Python version.

**Solutions:**

1. Open Command Prompt as Administrator
2. Upgrade Prophet:
   ```bash
   pip install --upgrade prophet
   ```
3. Verify the version:
   ```bash
   python -c "import prophet; print(prophet.__version__)"
   ```
   - Should show version 1.1.7 or higher
4. Restart ModelHub

### 4. "Insufficient data for Prophet forecasting"

**Symptoms:**
- Error shows: "Found: X data points, Required: At least 10 data points"

**Cause:**
Prophet requires a reasonable amount of historical data to detect patterns.

**Solutions:**

1. Load a dataset with more observations (minimum 10, ideally 30+)
2. Check your date range filter - it may be excluding too much data
3. For time series data, ensure you have:
   - At least several weeks of data for weekly patterns
   - At least several months for monthly patterns
   - At least 2 years for yearly seasonality

### 5. "Invalid date format in your data"

**Symptoms:**
- Error mentions date parsing or datetime
- Prophet cannot parse dates

**Cause:**
The date column contains invalid or unsupported date formats.

**Supported Date Formats:**
- `YYYY-MM-DD` (e.g., 2024-01-15)
- `DD/MM/YYYY` (e.g., 15/01/2024)
- `MM/DD/YYYY` (e.g., 01/15/2024)
- ISO format: `YYYY-MM-DDTHH:MM:SS`

**Solutions:**

1. Check your date column in the Data View tab
2. Ensure dates are consistent in format
3. Remove any:
   - Blank cells in the date column
   - Text that isn't a date
   - Invalid dates (e.g., 32/01/2024)
4. Excel dates should be formatted as text before import

### 6. "Python backend is not available"

**Symptoms:**
- Error shows backend unavailable on page load
- Cannot connect to http://localhost:8000

**Cause:**
Backend failed to start when ModelHub launched.

**Solutions:**

1. Check if another program is using port 8000:
   - Open Command Prompt
   - Run: `netstat -ano | findstr :8000`
   - If you see results, another app is using that port

2. Kill the process using port 8000:
   ```bash
   taskkill /F /PID [PID_NUMBER]
   ```
   - Replace [PID_NUMBER] with the number from the netstat command

3. Check Python installation:
   - Ensure Python is in your system PATH
   - Try running: `python --version` in Command Prompt

4. Check backend logs:
   - Look for errors in the terminal/console where ModelHub was launched
   - Check for missing dependencies or import errors

## Data Requirements for Best Results

### Minimum Requirements:
- **Data Points:** At least 10 observations
- **Time Span:** At least 2-3 cycles of your expected pattern
- **Data Quality:** No missing values in date or value columns

### Recommended for Quality Forecasts:
- **Data Points:** 50+ observations
- **Time Span:**
  - For weekly patterns: 6+ months of data
  - For yearly patterns: 2+ years of data
- **Frequency:** Regular intervals (daily, weekly, monthly)
- **Completeness:** Minimal gaps in the time series

## Testing Prophet Installation

To verify Prophet is working correctly:

1. Open Command Prompt
2. Run this test:
   ```bash
   python -c "from prophet import Prophet; import pandas as pd; print('Prophet is working!')"
   ```
3. If you see "Prophet is working!", the installation is correct
4. If you see an error, reinstall Prophet

## Advanced Troubleshooting

### Check Backend Health:
1. Open a web browser
2. Navigate to: http://localhost:8000/health
3. You should see:
   ```json
   {
     "status": "healthy",
     "dependencies": {
       "prophet": true,
       ...
     }
   }
   ```

### Manual Backend Start (for debugging):
1. Open Command Prompt
2. Navigate to the backend folder:
   ```bash
   cd "C:\Users\[YourUsername]\AppData\Local\Programs\modelling-mate\resources\app.asar.unpacked\backend\src"
   ```
3. Run:
   ```bash
   python main.py
   ```
4. Check for error messages
5. Keep this window open and launch ModelHub in a separate window

## Getting Help

If none of these solutions work:

1. Check the GitHub issues page
2. Collect this diagnostic information:
   - Python version: `python --version`
   - Prophet version: `python -c "import prophet; print(prophet.__version__)"`
   - ModelHub version (shown in About menu)
   - Full error message from "Show Technical Details"
   - Operating system version

3. Create a new issue with:
   - Description of the problem
   - What you were trying to do
   - Screenshots of the error
   - The diagnostic information above

## Known Issues

### Windows Username with Spaces
- **Issue:** Paths may fail if your Windows username contains spaces
- **Workaround:** The application should handle this automatically, but if issues persist, consider creating a new Windows user without spaces

### Antivirus Blocking Python
- **Issue:** Some antivirus software blocks Python execution
- **Workaround:** Add Python and ModelHub to your antivirus exceptions list

### Corporate Firewall
- **Issue:** Corporate firewalls may block localhost connections
- **Workaround:** Check with your IT department about allowing localhost:8000 connections
