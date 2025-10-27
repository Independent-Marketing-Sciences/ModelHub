# GitHub Releases Integration - Complete

## Changes Made

### 1. Removed Python Backend Popup Dialog ✅
**Problem:** Intrusive error dialog appeared at startup if Python backend failed to start

**Solution:**
- Disabled the popup dialog in [electron/main.js:260-263](electron/main.js#L260-L263)
- Application now logs a warning to console instead
- Users can still access setup instructions via Help > Documentation

**Code Change:**
```javascript
// Python backend error dialog disabled - users can check Help > Documentation for setup instructions
// The application will work without the Python backend for basic functionality
console.warn('Python backend failed to start, but continuing without popup dialog');
resolve();
```

### 2. Updated Documentation Link ✅
**Problem:** Documentation menu pointed to placeholder GitHub URL

**Solution:**
- Changed Help > Documentation to link to: https://github.com/Independent-Marketing-Sciences/ModelHub/releases
- Users can now access release notes, installers, and updates directly

**Code Change in [electron/main.js:389-393](electron/main.js#L389-L393):**
```javascript
{
  label: 'Documentation',
  click: () => {
    const { shell } = require('electron');
    shell.openExternal('https://github.com/Independent-Marketing-Sciences/ModelHub/releases');
  },
}
```

### 3. Configured Auto-Update for GitHub Releases ✅
**Problem:** Auto-updater was configured for OneDrive file share, not GitHub releases

**Solution:**
- Removed OneDrive path detection code
- Simplified auto-updater configuration to use GitHub releases
- electron-builder automatically configures update server when using `--publish always`
- Updates are now pulled from: https://github.com/Independent-Marketing-Sciences/ModelHub/releases

**Code Changes in [electron/main.js:12-18](electron/main.js#L12-L18):**
```javascript
// Configure auto-updater to use GitHub Releases
autoUpdater.autoDownload = false; // Don't auto-download, ask user first
autoUpdater.autoInstallOnAppQuit = true;

// Use GitHub Releases for updates (configured in electron-builder.yml)
// When electron-builder publishes with --publish always, it automatically configures the update server
console.log('Auto-updater configured to check GitHub releases');
```

### 4. Updated About Dialog ✅
**Bonus improvement:** About dialog now shows dynamic version from package.json

**Code Change:**
```javascript
const packageJson = require('../package.json');
dialog.showMessageBox(mainWindow, {
  type: 'info',
  title: 'About Modelling Mate',
  message: `Modelling Mate v${packageJson.version}`,
  detail:
    'Professional analytics and modeling platform\n\n' +
    'Independent Marketing Sciences\n' +
    '© 2025 IM Sciences Ltd',
});
```

## Publishing Workflow

### To Publish a New Release:

1. **Update version in package.json:**
   ```bash
   # Edit version number
   npm version patch  # or minor, or major
   ```

2. **Commit changes and create tag:**
   ```bash
   git add .
   git commit -m "Release v1.0.x"
   git tag v1.0.x
   git push origin main --tags
   ```

3. **Build and publish to GitHub releases:**
   ```bash
   npm run electron:publish:win
   ```

This will:
- Build the Next.js frontend
- Package with electron-builder
- Create installer: `Modelling Mate Setup X.X.X.exe`
- Create GitHub release automatically
- Upload installer and `latest.yml` to the release

### Manual GitHub Release Creation:

If you prefer to create the release manually:

1. Build installer:
   ```bash
   npm run electron:build:win
   ```

2. Go to: https://github.com/Independent-Marketing-Sciences/ModelHub/releases/new
3. Choose tag (e.g., v1.0.1)
4. Upload files from `dist/`:
   - `Modelling Mate Setup X.X.X.exe`
   - `latest.yml`

## How Auto-Update Works

1. User clicks **Help > Check for Updates**
2. App checks GitHub releases for newer version
3. If update available, shows dialog with download option
4. User can download and install immediately or later
5. Update installs when app closes (or immediately if user chooses "Restart Now")

## Configuration Files

- **electron-builder.yml:** Specifies GitHub as publish provider
  ```yaml
  publish:
    provider: github
    owner: Independent-Marketing-Sciences
    repo: ModelHub
    private: false
    releaseType: release
  ```

- **package.json:** Contains GH_TOKEN for publishing
  ```json
  "electron:publish:win": "set GH_TOKEN=... && ... --publish always"
  ```

- **.env.local:** Stores GitHub token securely (not committed to git)

## Testing

To test the changes:

1. Build production version: `npm run electron:build:win`
2. Install the app
3. Check Help menu:
   - Documentation should open GitHub releases
   - About should show correct version
   - Check for Updates should work (if a newer release exists)
4. Python backend errors should not show popup dialog

## Benefits

✅ No more intrusive Python backend error popup
✅ Users get updates from official GitHub releases
✅ Documentation link works correctly
✅ Automated release publishing with `npm run electron:publish:win`
✅ Professional update distribution workflow
