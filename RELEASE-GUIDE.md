# ModelHub v1.0.0 Release Guide

## Overview
This guide explains how to build, distribute, and update ModelHub v1.0.0 for end users.

---

## 📦 Building the Installer

### Prerequisites
1. Node.js and npm installed
2. Python 3.x installed (for backend)
3. All dependencies installed: `npm install`

### Build Commands

#### Windows Installer (NSIS)
```bash
npm run electron:build:win
```

This creates:
- `dist/Modelling Mate Setup 1.0.0.exe` - Full installer
- `dist/latest.yml` - Update metadata file

#### Mac Installer (if needed)
```bash
npm run electron:build:mac
```

#### Linux Installer (if needed)
```bash
npm run electron:build:linux
```

---

## 🚀 Distribution Options

### Option 1: GitHub Releases (RECOMMENDED)

**Best for:** Public or semi-public distribution, professional releases

#### Setup:
1. Create a GitHub repository for ModelHub (if not already done)
2. Update `electron-builder.yml`:
   ```yaml
   publish:
     provider: github
     owner: YOUR_GITHUB_USERNAME
     repo: ModelHub
     private: false  # Set to true for private repo
   ```
3. Generate a GitHub Personal Access Token:
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Create token with `repo` scope
   - Set environment variable: `GH_TOKEN=your_token_here`

#### Release Process:
```bash
# Set your GitHub token (Windows)
set GH_TOKEN=your_github_token_here

# Build and publish to GitHub Releases
npm run electron:build:win -- --publish always
```

#### Advantages:
✅ Automatic update distribution
✅ Free hosting
✅ Version history tracked
✅ Professional and reliable
✅ Users get updates automatically

#### User Installation:
1. Users download `Modelling Mate Setup 1.0.0.exe` from GitHub Releases
2. Run installer
3. App automatically checks for updates on startup

---

### Option 2: OneDrive/Network Share (CURRENT SETUP)

**Best for:** Internal company distribution, controlled access

#### Current Configuration:
- Update folder: `OneDrive - im-sciences.com/MasterDrive/Dev/04 - Python Modelling Toolkit/ModelHub-Updates`
- Auto-detects user's OneDrive path at runtime

#### Release Process:
```bash
# Build the installer
npm run electron:build:win

# Copy files to OneDrive update folder:
# - dist/Modelling Mate Setup 1.0.0.exe
# - dist/latest.yml
```

#### Advantages:
✅ Simple for internal distribution
✅ No external hosting needed
✅ Full control over who gets updates

#### Disadvantages:
⚠️ Users need OneDrive access
⚠️ Not suitable for public distribution
⚠️ Network dependent

---

### Option 3: Amazon S3 / Azure Blob Storage

**Best for:** Large-scale public distribution, professional deployment

#### Setup:
1. Create S3 bucket or Azure Blob container
2. Update `electron-builder.yml`:
   ```yaml
   publish:
     provider: s3
     bucket: your-bucket-name
     region: us-east-1
   ```
3. Set AWS credentials

#### Advantages:
✅ Scalable for thousands of users
✅ Fast CDN delivery worldwide
✅ Professional infrastructure

#### Disadvantages:
⚠️ Costs money (very cheap though, ~$1-5/month)
⚠️ More complex setup

---

## 🔄 Auto-Update System

### How It Works
1. **On App Startup:** App checks update server for `latest.yml`
2. **Version Check:** Compares current version (1.0.0) with server version
3. **User Prompt:** If update available, asks user to download
4. **Background Download:** Downloads update silently
5. **Install on Quit:** Update installs when user closes app

### Update Flow
```
App Starts → Check for Updates → Found Update?
                                      ↓
                                    Yes → Prompt User → Download → Install on Quit
                                      ↓
                                     No → Continue normally
```

### Configuration (in electron/main.js)
```javascript
autoUpdater.autoDownload = false; // Ask user first
autoUpdater.autoInstallOnAppQuit = true; // Install when app closes
```

---

## 📋 Release Checklist for v1.0.0

### Pre-Release
- [ ] Update version to 1.0.0 in `package.json` ✅ (Done)
- [ ] Test all features in development mode
- [ ] Test Python backend installation
- [ ] Update CHANGELOG.md with v1.0.0 changes
- [ ] Test build process locally

### Build & Test
- [ ] Run `npm run electron:build:win`
- [ ] Test installer on clean Windows machine
- [ ] Verify auto-update check works
- [ ] Test Python backend in production build
- [ ] Verify all features work in installed app

### Distribution
- [ ] Choose distribution method (GitHub/OneDrive/S3)
- [ ] Upload installer to chosen platform
- [ ] Upload `latest.yml` file (critical for updates!)
- [ ] Test installation from distribution source
- [ ] Document installation instructions for users

### Post-Release
- [ ] Monitor for user issues
- [ ] Create v1.0.1 when needed for bug fixes
- [ ] Plan v1.1.0 features

---

## 📝 Version Numbering

Follow Semantic Versioning (SemVer):

- **1.0.0** - Major release (breaking changes)
- **1.0.1** - Patch release (bug fixes)
- **1.1.0** - Minor release (new features, backwards compatible)
- **2.0.0** - Next major release

### Update Process:
1. Update version in `package.json`
2. Rebuild: `npm run electron:build:win`
3. Upload new files to update server
4. Users automatically notified of update

---

## 🛠️ Troubleshooting

### Users Not Getting Updates
1. Check `latest.yml` file is on update server
2. Verify app can reach update server URL
3. Check firewall/network settings
4. Review electron logs in app

### Build Fails
1. Delete `node_modules` and `dist` folders
2. Run `npm install` again
3. Try building again
4. Check for Python path issues

### Auto-Update Not Working
1. Verify `latest.yml` matches installer version
2. Check update server URL is accessible
3. Ensure app is properly code signed (or signing disabled)

---

## 🎯 Recommended Strategy for v1.0.0

**For Professional Launch:**

1. **Use GitHub Releases** (Option 1)
   - Most professional approach
   - Free and reliable
   - Industry standard

2. **Keep OneDrive as Backup** (Option 2)
   - For internal testing
   - Emergency distribution
   - Controlled rollouts

3. **Build Process:**
   ```bash
   # Update version
   # Test thoroughly
   npm run electron:build:win -- --publish always
   ```

4. **User Communication:**
   - Provide download link
   - Include installation guide
   - Explain auto-update feature
   - List system requirements

---

## 📦 What Users Receive

### Initial Installation
- `Modelling Mate Setup 1.0.0.exe` (approx 200-300MB)
- Includes all dependencies
- Installs to `C:\Program Files\Modelling Mate`
- Creates desktop shortcut

### System Requirements
- Windows 10/11 (64-bit)
- 4GB RAM minimum
- Python 3.8+ (for Prophet features)
- 500MB disk space

### Auto-Updates
- Automatic check on app startup
- User approval required for download
- Background download (doesn't block work)
- Installs when app closes
- No re-download of full installer

---

## 📞 Support

For questions or issues:
- Email: info@im-sciences.com
- Website: https://im-sciences.com

---

## 🎉 Congratulations on v1.0.0!

This is a significant milestone. The infrastructure is now in place for:
- Professional distribution
- Automatic updates
- Version control
- Scalable deployment

Good luck with your release! 🚀
