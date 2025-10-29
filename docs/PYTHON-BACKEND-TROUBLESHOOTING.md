# Python Backend Troubleshooting Guide

This guide helps you resolve issues with the Python backend that powers Prophet forecasting and advanced analytics features in Modelling Mate.

## Table of Contents
- [Quick Diagnostics](#quick-diagnostics)
- [Common Issues](#common-issues)
- [Installation Steps](#installation-steps)
- [Advanced Troubleshooting](#advanced-troubleshooting)
- [Getting Help](#getting-help)

---

## Quick Diagnostics

### Check Backend Status
1. Open Modelling Mate
2. Navigate to the **Prophet Seasonality** tab
3. Look for error messages at the top of the page
4. Click **"Show Technical Details"** to see specific error information

### Backend Status Meanings
- **not_started**: Backend hasn't been launched yet (app is starting)
- **starting**: Backend is currently starting up (wait 10-30 seconds)
- **running**: Backend is working correctly
- **failed**: Backend failed to start (see error message)
- **stopped**: Backend was running but has stopped

---

## Common Issues

### 1. Python Not Installed

**Error Message:**
```
Python is not installed or not in your system PATH
```

**Solution:**
1. Download Python 3.9, 3.10, or 3.11 from [python.org](https://www.python.org/downloads/)
   - **Important**: Do NOT use Python 3.12+ (Prophet compatibility issues)
   - **Recommended**: Python 3.11.x
2. During installation:
   - Check **"Add Python to PATH"** (very important!)
   - Choose "Install Now" or customize if needed
3. Restart your computer
4. Relaunch Modelling Mate
5. Click **"Restart Backend"** in the Prophet tab

**Verify Python Installation:**
```cmd
python --version
```
Should output: `Python 3.9.x`, `3.10.x`, or `3.11.x`

---

### 2. Missing Python Dependencies

**Error Messages:**
```
Missing required Python packages
ModuleNotFoundError: No module named 'prophet'
Backend started but did not respond to health checks
```

**Solution:**
1. Find the installation folder:
   - Default: `C:\Users\[YourUsername]\AppData\Local\Programs\modelling-mate\`
   - Or check the error message for the exact path
2. Navigate to the `scripts` folder
3. Right-click on **`Install-Dependencies.bat`**
4. Select **"Run as Administrator"**
5. Wait for installation to complete (5-15 minutes)
   - You'll see packages being installed
   - Prophet installation takes the longest
6. Restart Modelling Mate
7. Click **"Restart Backend"** in the Prophet tab

**What This Installs:**
- FastAPI (web framework)
- Uvicorn (server)
- Prophet (forecasting library)
- scikit-learn (regression)
- pandas, numpy, scipy (data processing)

---

### 3. Port 8000 Already In Use

**Error Message:**
```
Port 8000 is already in use
Another application is using the port needed by the Python backend
```

**Solution:**

**Option A - Close Other Applications:**
1. Close all other instances of Modelling Mate
2. Close any development servers (React, Flask, etc.) using port 8000
3. Restart Modelling Mate

**Option B - Find What's Using Port 8000:**
1. Open Command Prompt as Administrator
2. Run: `netstat -ano | findstr :8000`
3. Note the PID (last column)
4. Run: `tasklist | findstr [PID]`
5. Close that application or run: `taskkill /F /PID [PID]`
6. Restart Modelling Mate

---

### 4. Microsoft C++ Build Tools Missing

**Error Message:**
```
Prophet requires Microsoft C++ Build Tools on Windows
error: Microsoft Visual C++ 14.0 or greater is required
```

**Solution:**
1. Download Visual Studio Build Tools: [https://visualstudio.microsoft.com/downloads/](https://visualstudio.microsoft.com/downloads/)
2. Scroll down to "All Downloads" → "Tools for Visual Studio"
3. Download **"Build Tools for Visual Studio 2022"**
4. Run the installer
5. Select **"Desktop development with C++"**
6. Click Install (requires ~6GB)
7. Restart your computer
8. Run `Install-Dependencies.bat` again as Administrator
9. Restart Modelling Mate

**Alternative - Use Pre-built Prophet:**
Some Python distributions include pre-compiled packages that don't need build tools. Consider using Anaconda/Miniconda if you continue having issues.

---

### 5. Python Version Incompatibility

**Error Message:**
```
Python version is incompatible (requires 3.9-3.11)
Prophet library error
```

**Check Your Version:**
```cmd
python --version
```

**If You Have Python 3.12+:**
Prophet has compatibility issues with Python 3.12 and newer. You have two options:

**Option A - Install Python 3.11 (Recommended):**
1. Uninstall current Python (Settings → Apps → Python)
2. Download Python 3.11 from [python.org](https://www.python.org/downloads/)
3. Install with "Add to PATH" checked
4. Restart computer
5. Run `Install-Dependencies.bat` as Administrator
6. Restart Modelling Mate

**Option B - Use Virtual Environment:**
```cmd
# Install Python 3.11 alongside your current version
# Create virtual environment
python3.11 -m venv modelmate_env

# Activate it
modelmate_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

### 6. Backend Crashes Immediately

**Error Message:**
```
Python backend exited with code 1
The backend process exited unexpectedly
```

**Diagnostic Steps:**
1. Open Command Prompt
2. Navigate to the backend folder:
   ```cmd
   cd "C:\Users\[YourUsername]\AppData\Local\Programs\modelling-mate\resources\app.asar.unpacked\backend\src"
   ```
3. Try running the backend manually:
   ```cmd
   python main.py
   ```
4. Look for error messages that will help identify the issue

**Common Causes:**
- Missing dependencies → Run `Install-Dependencies.bat`
- Python version issue → Check version with `python --version`
- Corrupted installation → Reinstall Modelling Mate

---

### 7. Firewall or Antivirus Blocking

**Symptoms:**
- Backend starts but times out on health checks
- Connection refused errors
- Works sometimes but not others

**Solution:**
1. Open Windows Defender Firewall
2. Click "Allow an app through firewall"
3. Click "Change settings" (requires admin)
4. Click "Allow another app"
5. Browse to: `C:\Users\[YourUsername]\AppData\Local\Programs\modelling-mate\Modelling Mate.exe`
6. Check both "Private" and "Public"
7. Click OK
8. Restart Modelling Mate

**For Third-Party Antivirus:**
- Consult your antivirus documentation
- Add Modelling Mate to the exception/whitelist
- Allow local network connections on port 8000

---

## Installation Steps

### Fresh Installation

1. **Install Python 3.9-3.11**
   - Download from [python.org](https://www.python.org/downloads/)
   - Check "Add Python to PATH" during installation
   - Restart computer

2. **Install Microsoft C++ Build Tools** (if needed)
   - Download Build Tools for Visual Studio 2022
   - Install "Desktop development with C++"
   - Restart computer

3. **Install Modelling Mate**
   - Run the installer
   - Follow installation prompts

4. **Install Python Dependencies**
   - Navigate to: `C:\Users\[YourUsername]\AppData\Local\Programs\modelling-mate\scripts\`
   - Right-click `Install-Dependencies.bat`
   - Select "Run as Administrator"
   - Wait 10-15 minutes for installation

5. **Launch Modelling Mate**
   - The Python backend should start automatically
   - Check the Prophet tab to verify it's working

---

## Advanced Troubleshooting

### Manual Dependency Installation

If `Install-Dependencies.bat` fails, you can install manually:

```cmd
# Open Command Prompt as Administrator
pip install --upgrade pip

# Install dependencies one by one
pip install fastapi==0.115.6
pip install uvicorn[standard]==0.34.0
pip install pandas==2.2.3
pip install numpy==2.2.2
pip install scipy==1.15.2
pip install scikit-learn==1.6.1
pip install prophet==1.1.7  # This takes the longest

# Verify installation
python -c "import prophet; print('Prophet installed successfully!')"
```

### Check Backend Logs

**In Development Mode:**
Backend logs appear in the Electron console. To view:
1. Open Modelling Mate
2. Press `Ctrl+Shift+I` (Windows) or `Cmd+Option+I` (Mac)
3. Go to the Console tab
4. Look for messages starting with "Python Backend:"

**Check Health Endpoint Manually:**
1. Start Modelling Mate
2. Wait 30 seconds
3. Open browser to: `http://localhost:8000/health`
4. You should see JSON with status information
5. Check `http://localhost:8000/docs` for API documentation

### Reinstall Backend

If the backend is corrupted:

1. **Uninstall Modelling Mate**
   - Settings → Apps → Modelling Mate → Uninstall

2. **Delete Installation Folder**
   - `C:\Users\[YourUsername]\AppData\Local\Programs\modelling-mate\`

3. **Reinstall**
   - Run the Modelling Mate installer again
   - Follow installation steps above

### Use External Python Environment

For advanced users who want to manage their own Python environment:

1. Create a virtual environment with Python 3.9-3.11
2. Install dependencies using `requirements.txt`
3. Start the backend manually: `python backend/src/main.py`
4. Set environment variable: `NEXT_PUBLIC_PYTHON_BACKEND_URL=http://localhost:8000`
5. Launch Modelling Mate

---

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10/11, macOS 10.14+, or Linux
- **Python**: 3.9, 3.10, or 3.11 (NOT 3.12+)
- **RAM**: 4GB minimum, 8GB recommended
- **Disk Space**: 2GB for app + 1GB for Python dependencies
- **Network**: Port 8000 must be available on localhost

### Recommended Setup
- **Python**: 3.11.x (latest stable)
- **RAM**: 8GB or more
- **SSD**: For faster package installation and data loading
- **Admin Access**: Required for installing dependencies

---

## Getting Help

### Before Asking for Help

Please gather this information:

1. **Error Messages**
   - Full error text from Prophet tab
   - Technical details (click "Show Technical Details")

2. **System Information**
   - Windows/Mac/Linux version
   - Python version: `python --version`
   - Modelling Mate version (Help → About)

3. **What You've Tried**
   - List the troubleshooting steps you've already attempted
   - Any error messages from Command Prompt/Terminal

### Report an Issue

1. **GitHub Issues**: [https://github.com/Independent-Marketing-Sciences/ModelHub/issues](https://github.com/Independent-Marketing-Sciences/ModelHub/issues)
2. **Include**:
   - System information (above)
   - Screenshot of the error
   - Console logs (if possible)
   - Steps to reproduce the issue

### Quick Fixes Summary

| Issue | Quick Fix |
|-------|-----------|
| Python not found | Install Python 3.11, check "Add to PATH", restart computer |
| Missing packages | Run `Install-Dependencies.bat` as Administrator |
| Port in use | Close other instances of Modelling Mate |
| Build tools needed | Install Visual Studio Build Tools 2022 |
| Backend not responding | Click "Restart Backend" in Prophet tab |
| Version issues | Use Python 3.11 (NOT 3.12+) |

---

## FAQ

**Q: Do I need internet to use the Python backend?**
A: No, once dependencies are installed, the backend runs entirely offline on your local machine.

**Q: Can I use the app without the Python backend?**
A: Yes! Most features work without it. Only Prophet forecasting requires the backend.

**Q: Why does Prophet installation take so long?**
A: Prophet has complex dependencies and needs to compile C++ code. This is normal and can take 10-15 minutes.

**Q: Is my data sent anywhere?**
A: No. All processing happens locally on your machine. The backend runs on `localhost:8000` and never connects to external servers.

**Q: Can I use Python 3.12?**
A: Not recommended. Prophet has compatibility issues with Python 3.12+. Use Python 3.11 for best results.

**Q: The Restart Backend button isn't working. What now?**
A: Restart the entire Modelling Mate application. If that doesn't work, restart your computer and try again.

---

## Version History

- **v1.0.2** - Added backend status tracking, restart functionality, improved error messages
- **v1.0.1** - Initial Prophet integration
- **v1.0.0** - Initial release

---

For the latest updates and documentation, visit the [GitHub repository](https://github.com/Independent-Marketing-Sciences/ModelHub).
