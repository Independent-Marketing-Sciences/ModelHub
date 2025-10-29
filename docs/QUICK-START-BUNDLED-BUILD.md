# Quick Start: Building with Bundled Python Backend

This is a quick reference for building Modelling Mate with a bundled Python backend. For detailed information, see [BUNDLED-BACKEND-BUILD-GUIDE.md](BUNDLED-BACKEND-BUILD-GUIDE.md).

## Why Bundle Python?

**Problem**: Users have installation issues with Python, dependencies, and C++ Build Tools.

**Solution**: Bundle everything into the installer - users just install and run!

## Prerequisites (One-Time Setup)

On YOUR development machine:

1. **Python 3.11** installed
   - Download from [python.org](https://www.python.org/downloads/)
   - Check "Add Python to PATH"

2. **Install Python dependencies**:
   ```cmd
   cd backend
   pip install -r requirements.txt
   ```

3. **Node.js & npm** installed

## Building

### Option 1: Complete Build Script (Easiest)

```cmd
cd scripts
Complete-Build.bat
```

Wait 15-20 minutes. Done!

### Option 2: NPM Script

```cmd
npm run build:bundled
```

### Option 3: Manual Steps

```cmd
# 1. Build Python backend
cd scripts
build-python-backend.bat

# 2. Build Electron app
cd ..
npm run electron:build:win
```

## Output

After building:

```
dist/
├── Modelling Mate Setup 1.0.3.exe  (~200 MB)  ← Distribute this!
└── win-unpacked/                    (~600 MB)  ← For testing

backend/dist/
└── modelling-mate-backend/          (~500 MB)  ← Bundled backend
    ├── modelling-mate-backend.exe
    └── _internal/ (Python runtime + dependencies)
```

## Testing

### Quick Test

```cmd
# Test bundled backend standalone
cd backend\dist\modelling-mate-backend
modelling-mate-backend.exe

# In another terminal, test health endpoint
curl http://localhost:8000/health
```

Expected: `{"status": "healthy", ...}`

### Full Test

1. Install from `dist\Modelling Mate Setup X.X.X.exe`
2. Launch Modelling Mate
3. Open Prophet Seasonality tab
4. Should show "Backend available" (no errors)

### Test on Clean Machine

**Important**: Test on a machine WITHOUT Python installed to verify bundling works!

## Distributing

Just share the installer:
```
dist\Modelling Mate Setup 1.0.3.exe
```

Users:
1. Download installer
2. Run installer
3. Launch Modelling Mate
4. Everything works - no Python setup needed!

## Troubleshooting

### Build fails: "Python not found"

**Solution**: Install Python 3.11 on YOUR dev machine

### Build fails: "Module not found"

**Solution**:
```cmd
cd backend
pip install -r requirements.txt
```

### Backend bundle is missing

**Check**:
```cmd
dir backend\dist\modelling-mate-backend\modelling-mate-backend.exe
```

If missing, run:
```cmd
cd scripts
build-python-backend.bat
```

### Backend doesn't start in app

**Check app logs**:
1. Open Modelling Mate
2. Press `Ctrl+Shift+I`
3. Look for: `Bundled backend check: FOUND ✓`

If says "NOT FOUND", rebuild Python backend.

## Build Commands Reference

```cmd
# Build Python backend only
npm run build:python-backend

# Build complete app with bundled backend
npm run build:bundled

# Or use batch scripts
cd scripts
build-python-backend.bat      # Backend only
Complete-Build.bat            # Full build
```

## Size Comparison

| Build Type | Installer | Installed | Notes |
|------------|-----------|-----------|-------|
| Without bundle | ~50 MB | ~100 MB | Requires Python install |
| With bundle | ~200 MB | ~600 MB | No Python needed! |

The larger size is worth it - users have a much better experience!

## What's Included in Bundle?

The bundled backend contains:
- ✅ Python 3.11 runtime
- ✅ FastAPI + Uvicorn (web server)
- ✅ Prophet (forecasting) - **pre-compiled!**
- ✅ pandas, numpy, scipy (data processing)
- ✅ scikit-learn (regression)
- ✅ All other dependencies

**Users don't need to install anything!**

## Fallback Mode

If bundled backend is missing (e.g., during development), app falls back to system Python:

```
[Bundled Backend Missing]
        ↓
[Check System Python]
        ↓
    [Found?]
   ╱        ╲
 Yes         No
  ↓           ↓
Use it    Show error
```

This allows:
- Development without rebuilding
- Testing with different Python versions
- Troubleshooting

## Development Workflow

**For daily development** (no bundling needed):
```cmd
npm run electron:dev
```
Uses system Python + dependencies

**For releases** (with bundling):
```cmd
npm run build:bundled
```
Creates installer with bundled backend

## CI/CD

For GitHub Actions or automated builds:

```yaml
- name: Setup Python
  uses: actions/setup-python@v2
  with:
    python-version: '3.11'

- name: Build Bundled App
  run: npm run build:bundled
```

## Version Updates

When updating:

1. Update version in `package.json`
2. Rebuild:
   ```cmd
   npm run build:bundled
   ```
3. Test installer
4. Distribute new version

## Next Steps

1. **Build it**:
   ```cmd
   cd scripts
   Complete-Build.bat
   ```

2. **Test it** on a machine without Python

3. **Distribute it** to users!

---

## Quick Reference

| Task | Command |
|------|---------|
| Build backend only | `cd scripts && build-python-backend.bat` |
| Build complete app | `cd scripts && Complete-Build.bat` |
| Build via npm | `npm run build:bundled` |
| Test backend | `cd backend\dist\modelling-mate-backend && modelling-mate-backend.exe` |
| Test full app | Install from `dist\Modelling Mate Setup X.X.X.exe` |
| Dev mode (no bundle) | `npm run electron:dev` |

---

**Questions?** See [BUNDLED-BACKEND-BUILD-GUIDE.md](BUNDLED-BACKEND-BUILD-GUIDE.md) for details.

**Python issues?** See [PYTHON-BACKEND-TROUBLESHOOTING.md](PYTHON-BACKEND-TROUBLESHOOTING.md).
