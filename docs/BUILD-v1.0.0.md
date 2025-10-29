# Quick Build Guide for v1.0.0

## 🚀 Fast Track: Build Your First Release

### Step 1: Build the Installer
```bash
npm run electron:build:win
```

**Output:**
- `dist/Modelling Mate Setup 1.0.0.exe` ← Give this to users
- `dist/latest.yml` ← Needed for auto-updates

**Time:** ~5-10 minutes

---

### Step 2: Choose Your Distribution Method

#### Option A: GitHub Releases (Recommended)

**Best for:** Professional distribution, public or private

**Quick Setup:**
1. Create GitHub repo (if not done)
2. Get GitHub token: https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Select `repo` scope
   - Copy the token

3. Edit `electron-builder.yml`:
   ```yaml
   publish:
     provider: github
     owner: YOUR_GITHUB_USERNAME
     repo: ModelHub
     private: false
   ```

4. Build & publish:
   ```bash
   set GH_TOKEN=your_token_here
   npm run electron:build:win -- --publish always
   ```

**Done!** Users download from GitHub Releases page.

---

#### Option B: OneDrive (Current Setup)

**Best for:** Internal company use

**Quick Setup:**
1. Build: `npm run electron:build:win`
2. Copy these 2 files to OneDrive:
   - `dist/Modelling Mate Setup 1.0.0.exe`
   - `dist/latest.yml` ⚠️ **MUST include this for updates!**

**Folder:** `OneDrive - im-sciences.com/MasterDrive/Dev/04 - Python Modelling Toolkit/ModelHub-Updates`

**Done!** Share the .exe with users.

---

#### Option C: Simple File Share

**Best for:** Quick testing, small group

**Quick Setup:**
1. Build: `npm run electron:build:win`
2. Put `dist/Modelling Mate Setup 1.0.0.exe` on:
   - Network drive
   - Dropbox/Google Drive
   - Email (if < 25MB compressed)
   - USB drive

⚠️ **Note:** Without `latest.yml`, users won't get auto-updates.

---

## 📋 What to Give Users

### Minimum:
- `Modelling Mate Setup 1.0.0.exe`

### Recommended:
- `Modelling Mate Setup 1.0.0.exe`
- Installation instructions (see below)
- System requirements

---

## 📝 Simple Installation Instructions for Users

```
Modelling Mate v1.0.0 - Installation Guide

1. Download "Modelling Mate Setup 1.0.0.exe"
2. Double-click to run the installer
3. Follow the installation wizard
4. Launch Modelling Mate from desktop shortcut

System Requirements:
- Windows 10/11 (64-bit)
- 4GB RAM minimum
- 500MB disk space

Optional (for Prophet forecasting):
- Python 3.8 or newer
- Run Install-Dependencies.bat after installation

Questions? Contact: info@im-sciences.com
```

---

## 🔄 Future Updates (v1.0.1, v1.1.0, etc.)

### To Release an Update:

1. **Update version** in `package.json`:
   ```json
   "version": "1.0.1",
   ```

2. **Rebuild:**
   ```bash
   npm run electron:build:win
   ```

3. **Upload to same location** (GitHub or OneDrive)

4. **Users automatically notified** when they open the app!

---

## ⚡ Quick Commands Reference

```bash
# Build production installer
npm run electron:build:win

# Build and publish to GitHub
npm run electron:build:win -- --publish always

# Test in development
npm run electron:dev

# Run frontend only
npm run dev:frontend
```

---

## 🐛 Quick Troubleshooting

**Build fails?**
```bash
rmdir /s /q node_modules dist
npm install
npm run electron:build:win
```

**Need to rebuild everything?**
```bash
rmdir /s /q node_modules dist out .next
npm install
npm run electron:build:win
```

**Python backend not working?**
- Make sure `backend/` folder is included in build
- Check `electron-builder.yml` has `asarUnpack: backend/**/*`

---

## ✅ Pre-Release Checklist

- [ ] Version updated to 1.0.0 in package.json ✅
- [ ] All features tested in dev mode
- [ ] Build completes without errors
- [ ] Test installer on clean machine
- [ ] Auto-update system tested (if using)
- [ ] Installation instructions prepared
- [ ] Support contact info updated

---

## 🎯 Summary

**Minimal Path to v1.0.0:**
1. Run `npm run electron:build:win`
2. Share `dist/Modelling Mate Setup 1.0.0.exe`
3. Done!

**Professional Path:**
1. Set up GitHub repository
2. Configure GitHub token
3. Run build with `--publish always`
4. Share GitHub Releases link
5. Users get automatic updates!

---

**Ready to build? Let's go! 🚀**

```bash
npm run electron:build:win
```
