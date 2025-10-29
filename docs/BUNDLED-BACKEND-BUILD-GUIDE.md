# Bundled Python Backend Build Guide

This guide explains how to build Modelling Mate with a bundled Python backend using PyInstaller, eliminating the need for users to install Python separately.

## Overview

**Problem**: Users experience installation issues because they need to:
1. Install Python 3.9-3.11
2. Add Python to PATH
3. Run Install-Dependencies.bat
4. Install Microsoft C++ Build Tools (for Prophet)

**Solution**: Bundle Python and all dependencies into a single executable using PyInstaller
- Users don't need Python installed
- No dependency installation required
- No C++ Build Tools needed
- Just install and run!

## Architecture

### Before (System Python)
```
User's Machine
├── Modelling Mate.exe
│   └── Requires: System Python + Dependencies
└── User must install:
    ├── Python 3.9-3.11
    ├── pip install requirements.txt
    └── Microsoft C++ Build Tools
```

### After (Bundled Backend)
```
User's Machine
└── Modelling Mate.exe
    └── Contains:
        ├── Frontend (Electron + Next.js)
        └── Backend (Bundled Python + All Dependencies)
            ├── Python 3.11 runtime
            ├── FastAPI + Uvicorn
            ├── Prophet (pre-compiled)
            ├── pandas, numpy, scipy
            └── All other dependencies
```

## Build Process

### Prerequisites

**On YOUR Development Machine** (one-time setup):
1. Python 3.9-3.11 installed (Python 3.11 recommended)
2. All dependencies installed:
   ```cmd
   cd backend
   pip install -r requirements.txt
   ```
3. Node.js and npm installed
4. Git installed

### Step 1: Build the Python Backend Bundle

Run the build script:
```cmd
cd scripts
build-python-backend.bat
```

**What this does:**
1. Checks Python installation
2. Installs/upgrades all dependencies
3. Cleans previous builds
4. Runs PyInstaller with `main.spec`
5. Creates bundled executable: `backend/dist/modelling-mate-backend/`
6. Tests the bundled backend

**Expected output:**
```
Backend/dist/modelling-mate-backend/
├── modelling-mate-backend.exe  (main executable)
├── _internal/                  (Python runtime + dependencies)
│   ├── python311.dll
│   ├── prophet/
│   ├── pandas/
│   ├── numpy/
│   └── ... (all dependencies)
└── modules/                    (your backend code)
```

**Build time**: 5-10 minutes
**Size**: ~400-500 MB (includes full Python runtime + all packages)

### Step 2: Build the Electron Application

```cmd
npm run electron:build:win
```

**What this does:**
1. Builds Next.js frontend (`npm run build`)
2. Packages with electron-builder
3. Includes the bundled backend from `backend/dist/modelling-mate-backend/`
4. Creates installer: `dist/Modelling Mate Setup X.X.X.exe`

**Expected output:**
- Installer: `dist/Modelling Mate Setup X.X.X.exe` (~150-200 MB)
- Unpacked: `dist/win-unpacked/` (for testing)

### Complete Build Script

For convenience, here's a complete build script:

```cmd
REM Complete-Build.bat
@echo off
echo ========================================
echo Building Modelling Mate with Bundled Backend
echo ========================================
echo.

REM Step 1: Build Python backend
echo [1/3] Building Python backend bundle...
cd scripts
call build-python-backend.bat
if errorlevel 1 (
    echo ERROR: Python backend build failed
    pause
    exit /b 1
)
cd ..

REM Step 2: Build Next.js frontend
echo [2/3] Building Next.js frontend...
call npm run build
if errorlevel 1 (
    echo ERROR: Next.js build failed
    pause
    exit /b 1
)

REM Step 3: Build Electron installer
echo [3/3] Building Electron installer...
call npm run electron:build:win
if errorlevel 1 (
    echo ERROR: Electron build failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo Installer location: dist\Modelling Mate Setup X.X.X.exe
echo.
pause
```

## How It Works

### Application Startup Flow

1. **User launches Modelling Mate.exe**
2. **Electron main process starts** ([electron/main.js](electron/main.js))
3. **Backend detection:**
   ```javascript
   // Check for bundled backend first
   bundledPath = 'resources/app.asar.unpacked/backend/dist/modelling-mate-backend/modelling-mate-backend.exe'

   if (bundled backend exists) {
     Use bundled backend ✓ (no Python needed!)
   } else {
     Fallback to system Python (requires installation)
   }
   ```
4. **Backend startup:**
   - Bundled: Spawns `modelling-mate-backend.exe` directly
   - System: Spawns `python main.py` (requires Python + dependencies)
5. **Health check**: Waits for `http://localhost:8000/health`
6. **Frontend loads**: Prophet tab becomes available

### Bundling with PyInstaller

The [backend/main.spec](backend/main.spec) file configures PyInstaller:

```python
# Key configurations:
hiddenimports = [
    'uvicorn.logging',      # ASGI server
    'prophet',              # Forecasting library
    'pandas', 'numpy',      # Data processing
    # ... all dependencies
]

datas = [
    # Prophet includes Stan models (must be included)
    collect_data_files('prophet'),
    # Backend modules
    ('src/modules', 'modules'),
]

exe = EXE(
    # Creates standalone executable
    name='modelling-mate-backend',
    console=True,  # Keep console for logging
)

coll = COLLECT(
    # Bundles everything into dist/modelling-mate-backend/
)
```

### Electron Builder Integration

[electron-builder.yml](electron-builder.yml) includes the bundled backend:

```yaml
files:
  - backend/dist/modelling-mate-backend/**/*  # PyInstaller bundle
  - backend/src/**/*                          # Source (fallback)

asarUnpack:
  - backend/**/*  # Must unpack - executables can't run from ASAR
```

## Testing

### Test Bundled Backend Standalone

Before building the full app:

```cmd
cd backend\dist\modelling-mate-backend
modelling-mate-backend.exe

# In another terminal:
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "dependencies": {
    "prophet": true,
    "pandas": true,
    "numpy": true,
    "scipy": true,
    "sklearn": true
  }
}
```

### Test Full Application

1. **Development mode** (uses bundled backend if exists):
   ```cmd
   npm run electron:dev
   ```

2. **Production installer**:
   ```cmd
   cd dist
   "Modelling Mate Setup X.X.X.exe"
   # Install and run
   ```

3. **Check logs** (in app):
   - Open app
   - Press `Ctrl+Shift+I` (Dev Tools)
   - Check Console for:
     ```
     Bundled backend check: FOUND ✓
     Using BUNDLED Python backend (self-contained)
     ```

## Advantages

### For Users
- ✅ **No Python installation required**
- ✅ **No dependency management**
- ✅ **No C++ Build Tools needed**
- ✅ **Single installer** - just download and run
- ✅ **Faster startup** - no pip checks
- ✅ **More reliable** - consistent environment
- ✅ **Offline-ready** - no internet needed after download

### For Developers
- ✅ **Fewer support tickets** - "Python not found" is eliminated
- ✅ **Consistent environment** - everyone has same backend version
- ✅ **Easier deployment** - one file to distribute
- ✅ **Fallback available** - system Python still works if bundled backend missing

## Disadvantages & Trade-offs

### Increased Size
- **Bundled installer**: ~200 MB (vs ~50 MB without backend)
- **Installed size**: ~600 MB (vs ~100 MB without backend)
- **Reason**: Includes full Python runtime + Prophet + all dependencies

### Longer Build Time
- **Backend bundle**: 5-10 minutes (one-time per build)
- **Total build**: 15-20 minutes (vs 5 minutes without bundling)

### Platform-Specific
- Must build on Windows for Windows
- Must build on macOS for macOS
- Can't cross-compile easily

## Fallback Mode

The app still supports system Python as a fallback:

```javascript
if (bundled backend not found) {
  Check for system Python
  if (Python found) {
    Use system Python + Install-Dependencies.bat
  } else {
    Show error: "Neither bundled backend nor Python found"
  }
}
```

This allows:
- Development without rebuilding backend
- Users to update Python version if needed
- Troubleshooting with different Python versions

## Troubleshooting

### Build Fails: "Module not found"

**Problem**: PyInstaller can't find a dependency

**Solution**: Add to `hiddenimports` in [backend/main.spec](backend/main.spec):
```python
hiddenimports = [
    # ... existing imports ...
    'your_missing_module',
]
```

### Build Fails: "Data files missing"

**Problem**: Prophet needs Stan models, holidays data, etc.

**Solution**: Already handled in spec file:
```python
datas += collect_data_files('prophet')
datas += collect_data_files('holidays')
```

### Backend Crashes: "DLL not found"

**Problem**: Missing Windows DLL dependency

**Solution**: Install Visual C++ Redistributable on build machine

### Large Build Size

**Problem**: 500 MB is too big

**Solutions**:
1. Exclude unused packages in spec file:
   ```python
   excludes=['matplotlib', 'tkinter', 'PyQt5']
   ```
2. Use UPX compression (already enabled):
   ```python
   upx=True
   ```
3. Remove XGBoost if not needed (saves ~100 MB)

### Testing on Clean Machine

**Best practice**: Test installer on a machine WITHOUT Python installed

1. Use a VM or clean Windows install
2. Install Modelling Mate
3. Verify backend starts automatically
4. Check Prophet forecasting works

## Version Updates

When updating dependencies:

1. Update `backend/requirements.txt`
2. Rebuild backend bundle: `scripts\build-python-backend.bat`
3. Rebuild Electron app: `npm run electron:build:win`
4. Test thoroughly
5. Update version in `package.json`

## CI/CD Integration

For automated builds:

```yaml
# Example GitHub Actions workflow
name: Build with Bundled Backend

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest

    steps:
      - uses: actions/checkout@v2

      - name: Setup Python 3.11
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '18'

      - name: Build Python Backend
        run: |
          cd backend
          pip install -r requirements.txt
          python -m PyInstaller main.spec --clean

      - name: Build Electron App
        run: |
          npm install
          npm run build
          npm run electron:build:win

      - name: Upload Artifacts
        uses: actions/upload-artifact@v2
        with:
          name: installer
          path: dist/*.exe
```

## Summary

Bundling Python with PyInstaller solves installation issues by:
1. Eliminating need for Python installation
2. Including all dependencies (Prophet, pandas, etc.)
3. Providing self-contained executable
4. Maintaining fallback to system Python

**Build once on your machine → Distribute to users → They just install and run!**

No more "Python not found" or "Missing dependencies" errors!

## Files Modified/Created

### New Files
- [backend/main.spec](backend/main.spec) - PyInstaller configuration
- [scripts/build-python-backend.bat](scripts/build-python-backend.bat) - Build script
- This guide

### Modified Files
- [electron/main.js](electron/main.js) - Detects and uses bundled backend
- [electron-builder.yml](electron-builder.yml) - Includes bundled backend in installer
- [backend/requirements.txt](backend/requirements.txt) - Already includes pyinstaller

### Build Outputs (gitignored)
- `backend/dist/modelling-mate-backend/` - Bundled backend
- `backend/build/` - PyInstaller build cache
- `dist/` - Electron installer

## Next Steps

1. **Build the bundled backend**:
   ```cmd
   cd scripts
   build-python-backend.bat
   ```

2. **Build the full application**:
   ```cmd
   npm run electron:build:win
   ```

3. **Test on a clean machine** (no Python installed)

4. **Distribute the installer** - users just install and run!

---

For troubleshooting Python backend issues with the bundled version, see [PYTHON-BACKEND-TROUBLESHOOTING.md](PYTHON-BACKEND-TROUBLESHOOTING.md).
