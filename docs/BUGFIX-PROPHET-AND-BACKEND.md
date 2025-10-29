# Bug Fixes: Prophet Forecasting and Backend References

## Issues Resolved

### 1. Prophet "stan_backend" Error

**Problem:**
Users were encountering the error:
```
Error: 'Prophet' object has no attribute 'stan_backend'
```

**Root Cause:**
- Prophet version 1.1.6 has compatibility issues with Python 3.12
- The `stan_backend` attribute was removed/changed in the underlying cmdstanpy library

**Solution:**
- Updated Prophet from version 1.1.6 to 1.1.7
- Prophet 1.1.7 has full Python 3.12 compatibility
- File changed: `backend/requirements.txt`

**Testing:**
Prophet 1.1.7 successfully initializes and runs forecasts without the `stan_backend` error.

### 2. Incorrect "python-backend" Folder References

**Problem:**
Error messages and documentation were telling users to navigate to "python-backend" folder, but the actual folder is named "backend".

**Solution:**
Updated all references from "python-backend" to "backend" in:
- Error messages in CorrelationTab.tsx
- Documentation in README.md
- Documentation in backend/README.md
- .gitignore file

## Files Changed

1. `backend/requirements.txt` - Upgraded Prophet to 1.1.7
2. `src/features/correlation/components/CorrelationTab.tsx` - Fixed error message
3. `README.md` - Fixed installation instructions and folder structure
4. `backend/README.md` - Fixed installation instructions
5. `.gitignore` - Updated build artifact paths

## For Company Users

### If You Already Installed Prophet 1.1.6:

Run this command to upgrade:
```bash
pip install prophet==1.1.7
```

Or reinstall all dependencies:
```bash
cd backend
pip install -r requirements.txt
```

### If You Get "Python backend not running" Error:

The correct instructions are:
1. Open terminal in **backend** folder (not "python-backend")
2. Run: `python main.py`
3. Backend should run on http://localhost:8000

### Spaces in Username Issue

If your Windows username contains spaces (e.g., "Cameron Roberts"), this should not cause issues as long as:
- You're using the correct folder name: `backend`
- Python paths are properly quoted when needed (handled automatically by the application)

## Version Information

- Prophet: 1.1.6 → 1.1.7
- Python: 3.12 (fully compatible)
- All other dependencies: unchanged

## Next Steps

1. Pull the latest changes from the repository
2. Run `pip install -r backend/requirements.txt` to get Prophet 1.1.7
3. Restart the application

If you encounter any issues after applying these fixes, please report them with:
- The exact error message
- Your Python version (`python --version`)
- Your Prophet version (`python -c "import prophet; print(prophet.__version__)"`)
