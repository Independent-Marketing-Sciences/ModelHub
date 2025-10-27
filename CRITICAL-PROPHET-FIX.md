# CRITICAL: Prophet Installation Fix Required

## Issue Identified

**If you previously ran `Install-Dependencies.bat`, you may have the wrong version of Prophet installed.**

### The Problem:
- Install-Dependencies.bat was installing Prophet **1.1.6** (outdated)
- Prophet 1.1.6 has compatibility issues with Python 3.12
- This causes the `stan_backend` error that users have been experiencing
- The correct version is Prophet **1.1.7**

### Who This Affects:
- Anyone who ran Install-Dependencies.bat before this fix
- Users seeing `'Prophet' object has no attribute 'stan_backend'` errors
- Users on Python 3.12+ experiencing Prophet crashes

## Fix Instructions

### Option 1: Quick Fix (Recommended)

If you already have Prophet installed but it's not working:

1. Open **Command Prompt as Administrator**
2. Run this command:
   ```bash
   pip install --upgrade prophet==1.1.7
   ```
3. Wait for installation to complete (1-2 minutes)
4. Restart ModelHub
5. Test Prophet in the application

### Option 2: Complete Reinstall

If you want to reinstall all dependencies with the correct versions:

1. Ensure you have the latest version of ModelHub with the fixed Install-Dependencies.bat
2. Open **Command Prompt as Administrator**
3. First, uninstall the old Prophet:
   ```bash
   pip uninstall prophet -y
   ```
4. Navigate to the ModelHub installation folder
5. Run the updated Install-Dependencies.bat
6. Restart ModelHub

### Option 3: Manual Verification

Check if you have the correct version:

```bash
python -c "import prophet; print('Prophet version:', prophet.__version__)"
```

**Expected output:**
```
Prophet version: 1.1.7
```

**If you see 1.1.6 or any error, follow Option 1 above.**

## What Was Fixed

The following lines in `scripts/Install-Dependencies.bat` were updated:

```diff
- %PYTHON_CMD% -m pip install prophet==1.1.6
+ %PYTHON_CMD% -m pip install prophet==1.1.7
```

This change was applied to all 3 installation strategies in the batch file.

## Expected Results After Fix

After upgrading to Prophet 1.1.7:

✅ **No more `stan_backend` errors**
✅ **Full Python 3.12 compatibility**
✅ **Prophet forecasts work correctly**
✅ **Improved performance and stability**

## Still Having Issues?

If you still experience problems after upgrading:

1. Check the troubleshooting guide: [PROPHET-TROUBLESHOOTING.md](PROPHET-TROUBLESHOOTING.md)
2. Verify your Python version: `python --version`
   - Should be Python 3.8 or higher
3. Check if you have Microsoft C++ Build Tools installed (required on Windows)
4. Try a complete uninstall/reinstall of Prophet

## Timeline

- **Before this fix:** Prophet 1.1.6 installed (has issues)
- **After this fix:** Prophet 1.1.7 installed (works correctly)
- **Date of fix:** 2025-10-27

## For Developers

If you're building from source or packaging the application:

1. Ensure `requirements.txt` has `prophet==1.1.7` ✅ (already correct)
2. Ensure `Install-Dependencies.bat` installs `prophet==1.1.7` ✅ (now fixed)
3. Test installation on both Python 3.11 and 3.12
4. Verify Prophet loads without errors

## Questions?

If you need help or have questions about this fix:

1. Check the full documentation in [PROPHET-IMPROVEMENTS-v1.0.2.md](PROPHET-IMPROVEMENTS-v1.0.2.md)
2. Review the troubleshooting guide in [PROPHET-TROUBLESHOOTING.md](PROPHET-TROUBLESHOOTING.md)
3. Open an issue on GitHub with:
   - Your Python version
   - Your Prophet version (output of command above)
   - The exact error message you're seeing

---

**This is a critical fix that resolves the primary source of Prophet errors in ModelHub. All users should upgrade to Prophet 1.1.7.**
