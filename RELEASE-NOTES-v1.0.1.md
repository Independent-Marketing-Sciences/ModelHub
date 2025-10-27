# Release v1.0.1 - Prophet Compatibility Fixes

## Bug Fixes

### Prophet Forecasting
- **Fixed:** Upgraded Prophet from 1.1.6 to 1.1.7 for Python 3.12 compatibility
- **Fixed:** Resolved 'Prophet object has no attribute stan_backend' error
- Forecasting now works correctly with the latest Python version

### Documentation & Error Messages
- **Fixed:** Corrected all references from "python-backend" to "backend" folder
- **Fixed:** Updated error messages to show correct backend folder path
- **Fixed:** Updated installation instructions in README files
- **Fixed:** Updated .gitignore paths for build artifacts

### Build System
- **Fixed:** TypeScript build configuration to prevent Jest type errors

## Installation

### For New Users
Download and run the installer:
- **Windows:** Modelling Mate Setup 1.0.1.exe (235 MB)

### For Existing Users
If you have Prophet 1.1.6 installed, upgrade with:
```bash
pip install prophet==1.1.7
```

Or reinstall all dependencies:
```bash
cd backend
pip install -r requirements.txt
```

## Files Changed
- backend/requirements.txt: Prophet 1.1.6 → 1.1.7
- src/features/correlation/components/CorrelationTab.tsx: Fixed error message
- README.md: Fixed installation instructions
- backend/README.md: Fixed setup guide
- .gitignore: Updated paths
- tsconfig.json: Fixed TypeScript build configuration
- package.json: Version bump to 1.0.1

## Documentation
See BUGFIX-PROPHET-AND-BACKEND.md for detailed information about these fixes.

---

**Full Changelog**: https://github.com/Independent-Marketing-Sciences/ModelHub/compare/v1.0.0...v1.0.1

## Files to Upload to GitHub Release

1. `dist/Modelling Mate Setup 1.0.1.exe` - Windows installer (235 MB)
2. `dist/latest.yml` - Auto-update configuration file

## How to Create the GitHub Release

1. Go to: https://github.com/Independent-Marketing-Sciences/ModelHub/releases/new
2. Choose tag: **v1.0.1** (already pushed)
3. Release title: **Release v1.0.1 - Prophet Compatibility Fixes**
4. Copy the release notes above into the description
5. Upload the files listed above
6. Click "Publish release"
