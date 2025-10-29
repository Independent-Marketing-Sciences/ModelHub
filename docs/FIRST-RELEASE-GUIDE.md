# Publishing Your First Release - v1.0.2

## Current Situation

The auto-update system is **configured correctly** but showing 404 errors because **no releases have been published to GitHub yet**. This is expected behavior for a new application.

## What's Been Fixed

I've updated the error handling to provide better user feedback:

### Before (Error):
```
Update Check Failed
Unable to check for updates
Error: 404...
(Scary technical error message)
```

### After (Info):
```
No Releases Available
Update system is configured but no releases have been published yet

This is normal for a new application. Updates will be available
once the first release is published to GitHub.
```

## How to Publish Your First Release

### Step 1: Build the Installer

```bash
# Make sure version is set to 1.0.2 in package.json (already done ✅)

# Build the installer
npm run electron:build:win
```

This creates:
- `dist/Modelling Mate Setup 1.0.2.exe` - The installer
- `dist/latest.yml` - Update manifest file

### Step 2: Create GitHub Release

#### Option A: Using GitHub Web Interface (Easiest)

1. Go to: https://github.com/Independent-Marketing-Sciences/ModelHub
2. Click "Releases" (right sidebar)
3. Click "Create a new release"
4. Fill in:
   - **Tag:** `v1.0.2` (must start with 'v')
   - **Release title:** `Version 1.0.2`
   - **Description:** Paste the changelog below
5. Upload files:
   - `dist/Modelling Mate Setup 1.0.2.exe`
   - `dist/latest.yml`
6. Click "Publish release"

#### Option B: Using npm script (Automated)

```bash
# This builds AND publishes to GitHub in one step
npm run electron:publish:win
```

**Note:** This requires `GH_TOKEN` environment variable set (already in package.json)

### Step 3: Test Auto-Update

1. Install v1.0.2 from the installer
2. Click "Help > Check for Updates"
3. Should show: "You are running the latest version!"

Later, when you publish v1.0.3:
1. Users on v1.0.2 click "Help > Check for Updates"
2. Should offer to download v1.0.3

## Release Changelog for v1.0.2

Use this as the release description on GitHub:

```markdown
# ModelHub v1.0.2

## 🎉 New Features

### Charting Tab - Export Functionality
- **Export to Excel**: Download chart data as .xlsx file
- **Export as PNG**: High-quality chart image export
- **Copy to Clipboard**: One-click copy for pasting into presentations

### Outliers Tab - Enhanced Filtering
- **Regex Variable Filter**: Powerful pattern matching for variable selection
- **Visual Feedback**: Match counts and error messages
- **Consistent UX**: Matches Feature Extraction tab styling

### Auto-Update System
- **Download Progress**: Window title shows download percentage
- **Better Feedback**: Clear messages for all update scenarios
- **Smart Error Handling**: Helpful messages when updates unavailable

## 🐛 Bug Fixes

### Critical: Prophet Installation
- **Fixed Install-Dependencies.bat**: Now installs Prophet 1.1.7 (was 1.1.6)
- **Resolved stan_backend errors**: Version 1.1.7 fixes Python 3.12 compatibility
- **Better error messages**: Prophet errors now provide actionable guidance

### Prophet Feature Enhancements
- **Data Validation**: Checks for minimum 10 data points before forecasting
- **Backend Health Check**: Verifies backend availability before requests
- **Context-Aware Errors**: Specific error messages with solutions
- **Date Format Validation**: Clear guidance on supported date formats

## 📚 Documentation

New documentation files:
- **PROPHET-TROUBLESHOOTING.md**: Complete troubleshooting guide
- **PROPHET-IMPROVEMENTS-v1.0.2.md**: Technical details of Prophet fixes
- **AUTO-UPDATE-IMPROVEMENTS.md**: Auto-update system documentation
- **FEATURE-ENHANCEMENTS-v1.0.2.md**: New features documentation
- **FIRST-RELEASE-GUIDE.md**: This guide for publishing releases

## 🔧 Technical Changes

- Updated version: 1.0.1 → 1.0.2
- Added dependency: html2canvas for chart exports
- Enhanced error handling across multiple features
- Improved user feedback for all major features

## 📦 Installation

1. Download `Modelling Mate Setup 1.0.2.exe`
2. Run installer (may require administrator privileges)
3. Run `Install-Dependencies.bat` as Administrator
4. Launch Modelling Mate

## ⬆️ Upgrading from v1.0.1

The installer will automatically update your existing installation.

**Important for Prophet users:**
If you previously installed Prophet 1.1.6, upgrade to 1.1.7:
```bash
pip install --upgrade prophet==1.1.7
```

## 🆕 For New Users

See [README.md](README.md) for complete setup instructions.

---

**Full Changelog**: https://github.com/Independent-Marketing-Sciences/ModelHub/compare/v1.0.1...v1.0.2
```

## After Publishing

Once the release is published:

1. **Auto-update will work immediately**
   - Future users can update via "Help > Check for Updates"
   - Updates download and install automatically

2. **Error will be gone**
   - No more 404 errors
   - "Check for Updates" shows proper status

3. **For v1.0.3 and beyond**
   - Same process: build, tag, upload
   - Users on older versions get update notifications

## Troubleshooting

### "404 Not Found" Error

**Before first release:**
- ✅ Normal - no releases published yet
- ✅ App shows: "No Releases Available" (info message)

**After publishing release:**
- ❌ If still 404, check:
  - Is tag exactly `v1.0.2`? (must have 'v' prefix)
  - Are both files uploaded? (exe + latest.yml)
  - Is release published? (not draft)

### "Permission denied" when publishing

- Make sure `GH_TOKEN` is set
- Token needs `repo` permission
- For private repos, ensure token has access

### Auto-updater not finding update

Check electron-builder.yml has:
```yaml
publish:
  provider: github
  owner: Independent-Marketing-Sciences
  repo: ModelHub
```

## Repository Visibility

If the repository is **private:**
- Auto-updates work but require authentication
- GitHub token must be configured
- Consider making releases public

If the repository is **public:**
- Auto-updates work for everyone
- No authentication needed
- Recommended for distributed applications

## Next Steps

1. ✅ Build v1.0.2 installer
2. ✅ Create v1.0.2 release on GitHub
3. ✅ Upload exe + latest.yml files
4. ✅ Test update check
5. ✅ Distribute to users

After first release, subsequent releases are easier:
```bash
# Update version in package.json to 1.0.3
# Build and publish in one command:
npm run electron:publish:win
```

## Questions?

- Check [AUTO-UPDATE-IMPROVEMENTS.md](AUTO-UPDATE-IMPROVEMENTS.md) for technical details
- See [RELEASE-GUIDE.md](RELEASE-GUIDE.md) for ongoing release process
- GitHub releases docs: https://docs.github.com/en/repositories/releasing-projects-on-github
