# Auto-Update Improvements

## Overview

The "Check for Updates" feature in the Help menu has been significantly improved to provide better user feedback and a complete update experience.

## Changes Made

### 1. Manual Update Check Feedback

**Before:**
- Clicking "Check for Updates" showed a "Checking..." message
- No feedback when already on latest version
- No error messages if check failed
- Users were left wondering if it worked

**After:**
- ✅ Shows "You are running the latest version!" when up to date
- ✅ Displays current version number
- ✅ Shows detailed error messages if check fails
- ✅ Option to view releases page manually if network issues occur

### 2. Download Progress Indicator

**New Feature:**
- Window title shows download progress: "Modelling Mate - Downloading update... 45%"
- Console logs download speed and progress
- Visual feedback so users know download is happening

### 3. Error Handling

**Improved error messages:**
```
Unable to check for updates

Error: [specific error]

This could be due to:
- No internet connection
- GitHub servers are unavailable
- Network firewall blocking the connection

Please try again later or check the releases page manually.

[OK] [View Releases]
```

### 4. Event-Driven Architecture

**Implementation:**
- Uses `autoUpdater.manualCheck` flag to distinguish manual vs automatic checks
- Automatic checks (on startup, every 4 hours) run silently unless update found
- Manual checks (user clicks menu) always provide feedback

## User Experience Flow

### Scenario 1: Already Up to Date

1. User clicks "Help > Check for Updates"
2. Dialog shows: "Checking for updates..."
3. System checks GitHub releases
4. Dialog shows: "You are running the latest version! Current version: 1.0.1"

### Scenario 2: Update Available

1. User clicks "Help > Check for Updates"
2. Dialog shows: "Checking for updates..."
3. System finds new version
4. Dialog shows: "A new version (1.0.2) is available! Would you like to download it now?"
5. User clicks "Download"
6. Window title updates: "Modelling Mate - Downloading update... 23%"
7. When complete, dialog shows: "Version 1.0.2 has been downloaded! Would you like to restart now?"
8. User chooses "Restart Now" → App closes, installer runs, new version launches
9. OR user chooses "Later" → Update installs when app closes next time

### Scenario 3: Network Error

1. User clicks "Help > Check for Updates"
2. Dialog shows: "Checking for updates..."
3. Network error occurs
4. Dialog shows: "Unable to check for updates. Error: [details]. This could be due to: ..."
5. User can click "View Releases" to open GitHub releases page in browser

## Automatic Update Checks

**When automatic checks happen:**
- On app startup (production mode only)
- Every 4 hours while app is running

**Automatic check behavior:**
- Runs silently in background
- Only shows dialog if update is actually available
- No interruption to user if already up to date
- Errors logged to console only (no user dialogs)

## Technical Implementation

### Files Modified

**electron/main.js:**
- Line 319-347: Updated "Check for Updates" menu handler
- Line 443-456: Added dialog for "no updates available" (manual checks only)
- Line 468-477: Added download progress tracking
- Line 480-484: Reset window title when download complete
- Line 481-495: Enhanced error handling with user feedback

### Key Code Changes

**Manual check flag:**
```javascript
autoUpdater.manualCheck = true;
autoUpdater.checkForUpdates();
```

**Download progress:**
```javascript
autoUpdater.on('download-progress', (progressObj) => {
  mainWindow.setTitle(`Modelling Mate - Downloading update... ${Math.round(progressObj.percent)}%`);
});
```

**Smart feedback:**
```javascript
autoUpdater.on('update-not-available', (info) => {
  // Only show dialog if manual check
  if (autoUpdater.manualCheck) {
    dialog.showMessageBox(/* ... */);
    autoUpdater.manualCheck = false;
  }
});
```

## Configuration

### Auto-Updater Settings (in main.js)

```javascript
autoUpdater.autoDownload = false;        // Ask user before downloading
autoUpdater.autoInstallOnAppQuit = true; // Install when app closes
```

### Update Check Interval

```javascript
// Check every 4 hours
setInterval(() => {
  autoUpdater.checkForUpdates();
}, 4 * 60 * 60 * 1000);
```

## Testing

### Development Mode
- Update checking is disabled in dev mode
- Shows message: "Update checking is disabled in development mode"

### Production Mode Testing

**Test manual check:**
1. Build production version
2. Click "Help > Check for Updates"
3. Verify appropriate message appears

**Test update flow:**
1. Build version 1.0.1
2. Publish version 1.0.2 to GitHub releases
3. Run 1.0.1, click "Check for Updates"
4. Should offer to download 1.0.2
5. Download should show progress
6. After download, should offer to restart

**Test error handling:**
1. Disconnect from internet
2. Click "Check for Updates"
3. Should show error dialog with "View Releases" option

## Troubleshooting

### Updates Not Found

**Possible causes:**
- GitHub token not configured (for private repos)
- Release is draft or pre-release
- Version number in package.json not updated
- electron-builder.yml publish config incorrect

**Check:**
```javascript
// In console
autoUpdater.checkForUpdates().then(result => console.log(result));
```

### Download Fails

**Possible causes:**
- No latest.yml file in release assets
- .exe file missing from release
- Network/firewall blocking download

**Check GitHub release:**
- Should contain: `Modelling Mate Setup X.X.X.exe`
- Should contain: `latest.yml`

### Update Doesn't Install

**Possible causes:**
- User doesn't have admin rights
- Antivirus blocking installer
- Installer file corrupted

**Solution:**
- Run app as administrator
- Add exception in antivirus
- Re-download update

## Best Practices

### For Developers

1. **Always increment version** in package.json before building
2. **Create GitHub release** with proper tag (v1.0.1, v1.0.2, etc.)
3. **Test update flow** before announcing to users
4. **Include release notes** in GitHub release description

### For Users

1. **Keep app updated** for latest features and bug fixes
2. **Allow downloads** when prompted
3. **Restart when convenient** to apply updates
4. **Check manually** if you suspect app is outdated

## Future Enhancements

Potential improvements:

- [ ] Show changelog/release notes in update dialog
- [ ] Add settings to configure update check frequency
- [ ] Implement update channel selection (stable/beta)
- [ ] Add notification icon for pending updates
- [ ] Provide "Check on Startup" toggle in preferences
- [ ] Add rollback capability if update fails

## Version History

- **v1.0.0**: Basic auto-update implementation
- **v1.0.1**: Added GitHub releases integration
- **v1.0.2**: Enhanced update checking with user feedback (this version)

## Summary

The improved auto-update system provides:

✅ **Clear feedback** - Users always know what's happening
✅ **Progress indication** - Visual feedback during downloads
✅ **Error handling** - Helpful messages when things go wrong
✅ **User control** - Choice to download now or later
✅ **Non-intrusive** - Silent automatic checks, noisy only when needed
✅ **Reliable** - Robust error handling and retry options

Users should now have confidence that the update system is working and know exactly what to do when updates are available.
