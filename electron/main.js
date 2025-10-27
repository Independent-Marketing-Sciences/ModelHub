const { app, BrowserWindow, Menu, protocol, net, dialog, ipcMain } = require('electron');
const { autoUpdater } = require('electron-updater');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonBackend;
const isDev = process.env.NODE_ENV === 'development';
const port = process.env.PORT || 3000;
const pythonPort = 8000;

// Configure auto-updater to use GitHub Releases
autoUpdater.autoDownload = false; // Don't auto-download, ask user first
autoUpdater.autoInstallOnAppQuit = true;

// Use GitHub Releases for updates (configured in electron-builder.yml)
// When electron-builder publishes with --publish always, it automatically configures the update server
console.log('Auto-updater configured to check GitHub releases');

// Register custom protocol before app is ready
if (!isDev) {
  protocol.registerSchemesAsPrivileged([
    {
      scheme: 'app',
      privileges: {
        standard: true,
        secure: true,
        supportFetchAPI: true,
        corsEnabled: true
      }
    }
  ]);
}

function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 700,
    icon: path.join(__dirname, '../IMS_SiteIcon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js'),
    },
    title: 'Modelling Mate',
    backgroundColor: '#f8fafc',
    show: false, // Don't show until ready
  });

  // Show window when ready to prevent flashing
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Load the app
  if (isDev) {
    // Development mode: connect to Next.js dev server
    mainWindow.loadURL(`http://localhost:${port}`);
    // Open DevTools in development
    mainWindow.webContents.openDevTools();
  } else {
    // Production mode: load static files via custom protocol
    mainWindow.loadURL('app://./index.html');
  }

  // Create application menu
  createMenu();

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function checkPythonAvailable() {
  // Check if Python is available on the system
  return new Promise((resolve) => {
    const pythonExe = process.platform === 'win32' ? 'python' : 'python3';
    const checkPython = spawn(pythonExe, ['--version'], { shell: true });

    checkPython.on('error', () => resolve(false));
    checkPython.on('close', (code) => resolve(code === 0));

    // Timeout after 5 seconds
    setTimeout(() => resolve(false), 5000);
  });
}

function startPythonBackend() {
  // Start the Python FastAPI backend
  // In development: __dirname is /electron
  // In production: backend is unpacked to /resources/app.asar.unpacked/backend/src
  let pythonDir;
  let scriptsDir;

  if (isDev) {
    // Development: backend is next to electron folder
    pythonDir = path.join(__dirname, '../backend/src');
    scriptsDir = path.join(__dirname, '../scripts');
  } else {
    // Production: Use ASAR unpacked directory
    // When we use asarUnpack in electron-builder.yml, files are extracted to app.asar.unpacked
    const appPath = app.getAppPath(); // Gets resources/app.asar

    // Try unpacked location first (this is where asarUnpack puts files)
    pythonDir = path.join(appPath + '.unpacked', 'backend/src');
    scriptsDir = path.join(appPath + '.unpacked', 'scripts');

    // Log paths for debugging
    console.log('App path:', appPath);
    console.log('Python dir (unpacked):', pythonDir);
    console.log('Scripts dir (unpacked):', scriptsDir);
  }

  // Check if Python script exists first
  const pythonScript = path.join(pythonDir, 'main.py');
  const fs = require('fs');

  if (!fs.existsSync(pythonScript)) {
    console.error('Python script not found at:', pythonScript);
    console.error('Python dir:', pythonDir);
    console.error('Directory contents:', fs.existsSync(pythonDir) ? fs.readdirSync(pythonDir) : 'Directory does not exist');

    if (mainWindow) {
      dialog.showMessageBox(mainWindow, {
        type: 'error',
        title: 'Installation Error',
        message: 'Python backend files not found',
        detail: `The application files are incomplete or corrupted.\n\nExpected location: ${pythonScript}\n\nPlease reinstall the application.`,
        buttons: ['OK']
      });
    }
    return Promise.resolve();
  }

  // Determine Python executable path - try multiple options
  let pythonExe = 'python';
  if (process.platform !== 'win32') {
    pythonExe = 'python3';
  }

  console.log('Starting Python backend...');
  console.log('Python executable:', pythonExe);
  console.log('Python script:', pythonScript);
  console.log('Working directory:', pythonDir);

  // Always run Python script from source
  // Use 'cmd.exe' explicitly on Windows to avoid ENOENT error
  const spawnOptions = {
    cwd: pythonDir,
    shell: process.platform === 'win32' ? 'cmd.exe' : true,
  };

  pythonBackend = spawn(pythonExe, [pythonScript], spawnOptions);

  pythonBackend.stdout.on('data', (data) => {
    console.log(`Python Backend: ${data}`);
  });

  pythonBackend.stderr.on('data', (data) => {
    console.error(`Python Backend Error: ${data}`);
  });

  pythonBackend.on('error', (error) => {
    console.error('Failed to start Python backend:', error);

    // Show error dialog to user with option to run installer
    if (mainWindow) {
      const installScriptPath = path.join(scriptsDir, 'Install-Dependencies.bat');
      const scriptExists = require('fs').existsSync(installScriptPath);

      dialog.showMessageBox(mainWindow, {
        type: 'error',
        title: 'Python Backend Error',
        message: 'Failed to start the Python backend.',
        detail:
          'Please make sure:\n' +
          '1. Python 3.9-3.11 is installed\n' +
          '2. Python is added to your PATH\n' +
          '3. Required packages are installed\n\n' +
          `Error: ${error.message}`,
        buttons: scriptExists ? ['Run Dependency Installer', 'OK'] : ['OK'],
        defaultId: 0,
        cancelId: scriptExists ? 1 : 0,
      }).then((result) => {
        if (result.response === 0 && scriptExists) {
          // User clicked "Run Dependency Installer"
          const { shell } = require('electron');
          shell.openPath(installScriptPath);
        }
      });
    }
  });

  pythonBackend.on('close', (code) => {
    console.log(`Python backend exited with code ${code}`);
  });

  return new Promise((resolve) => {
    // Wait for backend to be ready
    const checkBackend = setInterval(async () => {
      try {
        const http = require('http');
        http.get(`http://localhost:${pythonPort}/health`, (res) => {
          if (res.statusCode === 200) {
            console.log('Python backend is ready!');
            clearInterval(checkBackend);
            resolve();
          }
        }).on('error', () => {
          // Backend not ready yet, keep checking
        });
      } catch (error) {
        // Backend not ready yet
      }
    }, 1000); // Check every second

    // Timeout after 30 seconds
    setTimeout(() => {
      clearInterval(checkBackend);
      console.warn('Python backend did not start in time');

      // Python backend error dialog disabled - users can check Help > Documentation for setup instructions
      // The application will work without the Python backend for basic functionality
      console.warn('Python backend failed to start, but continuing without popup dialog');
      resolve();
    }, 30000);
  });
}

function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Open Dataset',
          accelerator: 'CmdOrCtrl+O',
          click: () => {
            // TODO: Implement file open dialog
            console.log('Open dataset clicked');
          },
        },
        {
          label: 'Export to Excel',
          accelerator: 'CmdOrCtrl+E',
          click: () => {
            // TODO: Implement export
            console.log('Export clicked');
          },
        },
        { type: 'separator' },
        {
          label: 'Exit',
          accelerator: 'CmdOrCtrl+Q',
          click: () => {
            app.quit();
          },
        },
      ],
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { type: 'separator' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' },
      ],
    },
    {
      label: 'Tools',
      submenu: [
        {
          label: 'Install Python Dependencies',
          click: () => {
            const scriptsDir = isDev
              ? path.join(__dirname, '../scripts')
              : path.join(app.getAppPath() + '.unpacked', 'scripts');
            const installScriptPath = path.join(scriptsDir, 'Install-Dependencies.bat');

            if (require('fs').existsSync(installScriptPath)) {
              const { shell } = require('electron');
              shell.openPath(installScriptPath);
            } else {
              dialog.showMessageBox(mainWindow, {
                type: 'error',
                title: 'Script Not Found',
                message: 'Could not find Install-Dependencies.bat',
                detail: `Expected location: ${installScriptPath}`,
              });
            }
          },
        },
        { type: 'separator' },
        {
          label: 'Open Installation Folder',
          click: () => {
            const { shell } = require('electron');
            const installDir = isDev ? __dirname : app.getAppPath();
            shell.openPath(path.dirname(installDir));
          },
        },
      ],
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'Check for Updates',
          click: () => {
            if (isDev) {
              dialog.showMessageBox(mainWindow, {
                type: 'info',
                title: 'Updates',
                message: 'Update checking is disabled in development mode',
                detail: 'Build a production version to test auto-updates.',
              });
            } else {
              // Set flag to indicate this is a manual check
              autoUpdater.manualCheck = true;

              // Show checking message
              const checkingDialog = dialog.showMessageBox(mainWindow, {
                type: 'info',
                title: 'Checking for Updates',
                message: 'Checking for updates...',
                detail: 'Please wait while we check for the latest version.',
                buttons: ['Cancel']
              });

              // Check for updates
              autoUpdater.checkForUpdates().catch((error) => {
                console.error('Manual update check failed:', error);
              });
            }
          },
        },
        { type: 'separator' },
        {
          label: 'About Modelling Mate',
          click: () => {
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
          },
        },
        {
          label: 'Documentation',
          click: () => {
            const { shell } = require('electron');
            shell.openExternal('https://github.com/Independent-Marketing-Sciences/ModelHub/releases');
          },
        },
      ],
    },
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// IPC Handlers
ipcMain.handle('dialog:openFile', async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: [
      { name: 'Data Files', extensions: ['csv', 'xlsx', 'xls'] },
      { name: 'CSV Files', extensions: ['csv'] },
      { name: 'Excel Files', extensions: ['xlsx', 'xls'] },
      { name: 'All Files', extensions: ['*'] }
    ]
  });

  if (canceled) {
    return null;
  } else {
    return filePaths[0];
  }
});

ipcMain.handle('file:read', async (event, filePath) => {
  const fs = require('fs');
  try {
    const buffer = fs.readFileSync(filePath);
    // Convert buffer to base64 for safe transmission
    return buffer.toString('base64');
  } catch (error) {
    console.error('Error reading file:', error);
    throw error;
  }
});

ipcMain.handle('app:getVersion', () => {
  return app.getVersion();
});

// Auto-updater functions
function setupAutoUpdater() {
  // Only check for updates in production
  if (isDev) {
    return;
  }

  // Check for updates when app starts
  autoUpdater.checkForUpdates();

  // When update is available
  autoUpdater.on('update-available', (info) => {
    dialog.showMessageBox(mainWindow, {
      type: 'info',
      title: 'Update Available',
      message: `A new version (${info.version}) is available!`,
      detail: 'Would you like to download it now? The update will be installed when you close the app.',
      buttons: ['Download', 'Later'],
      defaultId: 0,
      cancelId: 1
    }).then((result) => {
      if (result.response === 0) {
        autoUpdater.downloadUpdate();

        // Show downloading progress
        dialog.showMessageBox(mainWindow, {
          type: 'info',
          title: 'Downloading Update',
          message: 'Downloading update in the background...',
          detail: 'You can continue working. The update will be installed when you close the app.',
          buttons: ['OK']
        });
      }
    });
  });

  // When no update is available
  autoUpdater.on('update-not-available', (info) => {
    console.log('App is up to date');

    // Only show dialog if this was a manual check (not automatic)
    if (autoUpdater.manualCheck) {
      dialog.showMessageBox(mainWindow, {
        type: 'info',
        title: 'No Updates Available',
        message: 'You are running the latest version!',
        detail: `Current version: ${app.getVersion()}\n\nYour application is up to date.`,
        buttons: ['OK']
      });
      autoUpdater.manualCheck = false; // Reset flag
    }
  });

  // Track download progress
  autoUpdater.on('download-progress', (progressObj) => {
    const logMessage = `Download speed: ${progressObj.bytesPerSecond} - Downloaded ${progressObj.percent}% (${progressObj.transferred}/${progressObj.total})`;
    console.log(logMessage);

    // Update window title to show progress
    if (mainWindow) {
      mainWindow.setTitle(`Modelling Mate - Downloading update... ${Math.round(progressObj.percent)}%`);
    }
  });

  // When update is downloaded
  autoUpdater.on('update-downloaded', (info) => {
    // Reset window title
    if (mainWindow) {
      mainWindow.setTitle('Modelling Mate');
    }

    dialog.showMessageBox(mainWindow, {
      type: 'info',
      title: 'Update Ready',
      message: `Version ${info.version} has been downloaded!`,
      detail: 'The update will be installed automatically when you close the app. Would you like to restart now?',
      buttons: ['Restart Now', 'Later'],
      defaultId: 0,
      cancelId: 1
    }).then((result) => {
      if (result.response === 0) {
        autoUpdater.quitAndInstall();
      }
    });
  });

  // Handle errors
  autoUpdater.on('error', (error) => {
    console.error('Auto-updater error:', error);

    // Show error dialog if this was a manual check
    if (autoUpdater.manualCheck) {
      dialog.showMessageBox(mainWindow, {
        type: 'error',
        title: 'Update Check Failed',
        message: 'Unable to check for updates',
        detail: `Error: ${error.message}\n\nThis could be due to:\n- No internet connection\n- GitHub servers are unavailable\n- Network firewall blocking the connection\n\nPlease try again later or check the releases page manually.`,
        buttons: ['OK', 'View Releases']
      }).then((result) => {
        if (result.response === 1) {
          const { shell } = require('electron');
          shell.openExternal('https://github.com/Independent-Marketing-Sciences/ModelHub/releases');
        }
      });
      autoUpdater.manualCheck = false; // Reset flag
    }
  });

  // Check for updates every 4 hours
  setInterval(() => {
    autoUpdater.checkForUpdates();
  }, 4 * 60 * 60 * 1000);
}

// App lifecycle
app.whenReady().then(async () => {
  // In production, register protocol to serve static files
  if (!isDev) {
    protocol.handle('app', (request) => {
      const filePath = request.url.replace('app://./', '');
      const outPath = path.join(__dirname, '../out', filePath);

      console.log('Protocol request:', request.url);
      console.log('Serving file:', outPath);

      return net.fetch(`file://${outPath}`);
    });
  }

  // Start Python backend for Prophet forecasting
  await startPythonBackend();

  // Create window
  createWindow();

  // Setup auto-updater
  setupAutoUpdater();

  app.on('activate', () => {
    // On macOS, re-create window when dock icon is clicked
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// Quit when all windows are closed (except on macOS)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Kill servers when app quits
app.on('before-quit', () => {
  if (pythonBackend) {
    pythonBackend.kill();
  }
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
});

process.on('unhandledRejection', (error) => {
  console.error('Unhandled Rejection:', error);
});
