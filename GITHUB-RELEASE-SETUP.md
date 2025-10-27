# GitHub Releases Setup Guide

## 🎯 Quick Start: Deploy v1.0.0 to GitHub Releases

Your app is now configured to publish to:
**https://github.com/Independent-Marketing-Sciences/ModelHub**

---

## Step 1: Create GitHub Personal Access Token

You need a token to allow electron-builder to publish releases.

### Get Your Token:

1. **Go to GitHub Token Settings:**
   https://github.com/settings/tokens

2. **Click "Generate new token (classic)"**

3. **Configure the token:**
   - **Name:** `ModelHub Release Publisher`
   - **Expiration:** `No expiration` (or 1 year if preferred)
   - **Scopes:** Check these boxes:
     - ✅ `repo` (Full control of private repositories)
       - This includes: repo:status, repo_deployment, public_repo, repo:invite, security_events

4. **Click "Generate token"**
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
5. **Copy the token immediately!** (You won't see it again)
   - It looks like: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

6. **Save it somewhere safe** (password manager, secure note)

---

## Step 2: Set Environment Variable

### Windows (Current Session):
```cmd
set GH_TOKEN=ghp_your_token_here
```

### Windows (Permanent):
```cmd
setx GH_TOKEN "ghp_your_token_here"
```
*Note: Close and reopen your terminal after this*

### PowerShell:
```powershell
$env:GH_TOKEN="ghp_your_token_here"
```

### Verify it's set:
```cmd
echo %GH_TOKEN%
```
Should display your token.

---

## Step 3: Build and Publish v1.0.0

### Option A: Build and Publish in One Command (Recommended)

```bash
npm run electron:build:win -- --publish always
```

This will:
1. ✅ Build the Next.js frontend
2. ✅ Package the Electron app
3. ✅ Create the installer
4. ✅ Upload to GitHub Releases
5. ✅ Create release with changelog

**Time:** ~10-15 minutes

---

### Option B: Build First, Publish Later

```bash
# Build only (no publish)
npm run electron:build:win

# Then publish manually if build succeeds
npm run electron:build:win -- --publish always
```

---

## Step 4: Verify the Release

1. **Go to your releases page:**
   https://github.com/Independent-Marketing-Sciences/ModelHub/releases

2. **You should see:**
   - Release tagged `v1.0.0`
   - `Modelling.Mate.Setup.1.0.0.exe` (installer file)
   - `latest.yml` (update manifest)

3. **Release will be marked as "Latest"**

---

## What Gets Published?

### Files Uploaded to GitHub:
- `Modelling Mate Setup 1.0.0.exe` (~200-400MB)
  - Full installer for users
  - Includes all dependencies

- `latest.yml` (~500 bytes)
  - Update manifest
  - Tells existing apps about new version
  - **Critical for auto-updates!**

### Release Information:
- **Tag:** v1.0.0
- **Name:** v1.0.0 or "Modelling Mate v1.0.0"
- **Body:** Auto-generated from commits or CHANGELOG.md
- **Assets:** Installer + manifest files

---

## How Users Get the App

### Initial Installation:

1. **Send users this link:**
   ```
   https://github.com/Independent-Marketing-Sciences/ModelHub/releases/latest
   ```

2. **Users download:** `Modelling Mate Setup 1.0.0.exe`

3. **Users run the installer**

4. **Done!** App is installed and configured for auto-updates

---

### Future Updates (Automatic):

1. **You release v1.0.1, v1.1.0, etc.**

2. **Users open the app**

3. **App automatically checks GitHub for updates**

4. **Dialog appears:** "Version 1.0.1 is available. Download now?"

5. **User clicks "Download"**

6. **Update downloads in background**

7. **User closes app → Update installs automatically**

8. **User opens app → Now on latest version!**

**Users never have to manually download updates again!** 🎉

---

## Releasing Future Versions

### For v1.0.1 (Bug Fixes):

1. **Update version in package.json:**
   ```json
   "version": "1.0.1",
   ```

2. **Update CHANGELOG.md** with changes

3. **Build and publish:**
   ```bash
   set GH_TOKEN=your_token
   npm run electron:build:win -- --publish always
   ```

4. **Done!** Existing users will be notified automatically.

---

### For v1.1.0 (New Features):

Same process, just update version to `1.1.0`

---

## Troubleshooting

### ❌ Error: "GitHub token is not set"

**Fix:**
```bash
set GH_TOKEN=ghp_your_token_here
```
Make sure there are no quotes around the token.

---

### ❌ Error: "Resource not accessible by integration"

**Fix:**
- Check your token has `repo` scope
- Regenerate token with correct permissions
- Make sure you have write access to the repository

---

### ❌ Error: "Cannot find module electron-builder"

**Fix:**
```bash
npm install
```

---

### ❌ Build succeeds but doesn't publish

**Check:**
1. GH_TOKEN is set: `echo %GH_TOKEN%`
2. You used `--publish always` flag
3. Token hasn't expired
4. You have push access to the repo

---

### ❌ Users not getting auto-updates

**Check:**
1. `latest.yml` is in the GitHub release assets
2. Release is marked as "Latest" (not pre-release)
3. User's app is connected to internet
4. User's firewall allows GitHub access

---

## Publishing Checklist

Before running the publish command:

- [ ] Version updated in package.json (e.g., 1.0.0)
- [ ] CHANGELOG.md updated with changes
- [ ] All features tested locally
- [ ] GH_TOKEN environment variable set
- [ ] Git changes committed (optional but recommended)
- [ ] Internet connection active

Then run:
```bash
npm run electron:build:win -- --publish always
```

Wait 10-15 minutes, then check GitHub releases page!

---

## Advanced: Draft Releases

Want to review before publishing?

```bash
# Publish as draft (not visible to users)
npm run electron:build:win -- --publish always

# Then manually edit the release on GitHub:
# - Edit release notes
# - Add screenshots
# - Click "Publish release" when ready
```

---

## Advanced: Pre-releases (Beta versions)

For testing versions:

1. **Use version like:** `1.1.0-beta.1`

2. **In electron-builder.yml:**
   ```yaml
   publish:
     provider: github
     owner: Independent-Marketing-Sciences
     repo: ModelHub
     private: false
     releaseType: prerelease
   ```

3. **Build and publish**

4. **Users won't auto-update to pre-releases** (safe for testing!)

---

## Repository Settings

### Recommended Settings:

1. **Go to repository settings:**
   https://github.com/Independent-Marketing-Sciences/ModelHub/settings

2. **General:**
   - Make sure repository is Public (or Private if preferred)
   - Enable "Issues" for bug reports

3. **Releases:**
   - No special configuration needed
   - electron-builder handles everything

---

## Security Notes

### About the GitHub Token:

- ✅ **Keep it secret!** Don't commit to git
- ✅ Store in environment variable or password manager
- ✅ Only use on your build machine
- ✅ Regenerate if compromised

### About Code Signing:

Currently disabled (`forceCodeSigning: false`). This means:
- ⚠️ Windows Defender might show warning on first install
- ⚠️ Users might need to click "More info" → "Run anyway"

**Future:** Consider getting code signing certificate for production.

---

## Quick Command Reference

```bash
# Set token (Windows CMD)
set GH_TOKEN=ghp_your_token_here

# Build and publish
npm run electron:build:win -- --publish always

# Build only (no publish)
npm run electron:build:win

# Check if token is set
echo %GH_TOKEN%

# Test build (development)
npm run electron:dev
```

---

## Success Indicators

✅ **Build succeeded if you see:**
```
• building        target=nsis file=dist\Modelling Mate Setup 1.0.0.exe
• publishing      file=Modelling Mate Setup 1.0.0.exe
• published       file=Modelling Mate Setup 1.0.0.exe
• published       file=latest.yml
```

✅ **Check GitHub releases page:**
https://github.com/Independent-Marketing-Sciences/ModelHub/releases

✅ **Should see your release with 2 files:**
- Installer (.exe)
- Manifest (latest.yml)

---

## User Distribution Instructions

**Share this with your users:**

```
Download Modelling Mate v1.0.0

1. Go to: https://github.com/Independent-Marketing-Sciences/ModelHub/releases/latest

2. Download "Modelling Mate Setup 1.0.0.exe"

3. Run the installer

4. Launch Modelling Mate from your desktop

The app will automatically check for updates when you open it.

System Requirements:
- Windows 10/11 (64-bit)
- 4GB RAM
- 500MB disk space

Support: info@im-sciences.com
```

---

## 🚀 Ready to Deploy?

### Final Steps:

1. **Set your GitHub token:**
   ```bash
   set GH_TOKEN=ghp_your_token_here
   ```

2. **Run the build:**
   ```bash
   npm run electron:build:win -- --publish always
   ```

3. **Wait 10-15 minutes** ☕

4. **Check releases page:**
   https://github.com/Independent-Marketing-Sciences/ModelHub/releases

5. **Share the link with users!** 🎉

---

**You're all set for v1.0.0 deployment!** 🚀
