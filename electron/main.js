const { app, BrowserWindow, Menu, protocol, net, dialog, ipcMain } = require('electron');
const { autoUpdater } = require('electron-updater');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

let mainWindow;
let pythonBackend;
let pythonBackendStatus = 'not_started'; // not_started, starting, running, failed, stopped
let pythonBackendError = null;
let pythonBackendStartAttempts = 0;
const MAX_START_ATTEMPTS = 3;
const isDev = process.env.NODE_ENV === 'development';
const port = process.env.PORT || 3000;
const pythonPort = 8000;

// Setup logging to file for debugging production issues
const logFilePath = path.join(app.getPath('userData'), 'modelling-mate.log');
const logStream = fs.createWriteStream(logFilePath, { flags: 'a' });

// Store original console methods
const originalConsoleLog = console.log;
const originalConsoleError = console.error;

function logToFile(message) {
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] ${message}\n`;
  logStream.write(logMessage);
  originalConsoleLog(message); // Use original console.log
}

// Override console methods to also log to file
console.log = function(...args) {
  const message = args.join(' ');
  logToFile(message);
};

console.error = function(...args) {
  const message = 'ERROR: ' + args.join(' ');
  logToFile(message);
};

logToFile('='.repeat(80));
logToFile('Modelling Mate Starting');
logToFile(`Version: ${app.getVersion()}`);
logToFile(`Platform: ${process.platform} ${process.arch}`);
logToFile(`Node: ${process.versions.node}, Electron: ${process.versions.electron}`);
logToFile(`User Data: ${app.getPath('userData')}`);
logToFile(`Log File: ${logFilePath}`);

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

async function checkPythonInstalled() {
  // Check if Python is installed and accessible
  return new Promise((resolve) => {
    const pythonExe = process.platform === 'win32' ? 'python' : 'python3';
    const checkProcess = spawn(pythonExe, ['--version'], {
      shell: process.platform === 'win32' ? 'cmd.exe' : true
    });

    let versionOutput = '';

    checkProcess.stdout.on('data', (data) => {
      versionOutput += data.toString();
    });

    checkProcess.stderr.on('data', (data) => {
      versionOutput += data.toString();
    });

    checkProcess.on('close', (code) => {
      if (code === 0 && versionOutput) {
        console.log('Python found:', versionOutput.trim());
        resolve({ installed: true, version: versionOutput.trim() });
      } else {
        console.error('Python not found or not accessible');
        resolve({ installed: false, error: 'Python not found in PATH' });
      }
    });

    checkProcess.on('error', (error) => {
      console.error('Error checking Python:', error);
      resolve({ installed: false, error: error.message });
    });

    // Timeout after 5 seconds
    setTimeout(() => {
      checkProcess.kill();
      resolve({ installed: false, error: 'Python check timed out' });
    }, 5000);
  });
}

async function checkPortAvailable(port) {
  // Check if a port is already in use
  return new Promise((resolve) => {
    const http = require('http');
    const server = http.createServer();

    server.once('error', (err) => {
      if (err.code === 'EADDRINUSE') {
        resolve({ available: false, error: `Port ${port} is already in use` });
      } else {
        resolve({ available: false, error: err.message });
      }
    });

    server.once('listening', () => {
      server.close();
      resolve({ available: true });
    });

    server.listen(port);
  });
}

function startPythonBackend() {
  pythonBackendStartAttempts++;

  if (pythonBackendStartAttempts > MAX_START_ATTEMPTS) {
    console.error(`Failed to start Python backend after ${MAX_START_ATTEMPTS} attempts`);
    pythonBackendStatus = 'failed';
    pythonBackendError = `Failed after ${MAX_START_ATTEMPTS} attempts`;
    return Promise.resolve();
  }

  pythonBackendStatus = 'starting';
  pythonBackendError = null;

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

  if (!fs.existsSync(pythonScript)) {
    console.error('Python script not found at:', pythonScript);
    console.error('Python dir:', pythonDir);
    console.error('Directory contents:', fs.existsSync(pythonDir) ? fs.readdirSync(pythonDir) : 'Directory does not exist');

    pythonBackendStatus = 'failed';
    pythonBackendError = `Backend files not found at ${pythonScript}`;

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

  return new Promise(async (resolve) => {
    console.log('Starting Python backend...');
    console.log('Running pre-flight checks...');

    // Check for port availability first (applies to both bundled and system Python)
    const portCheck = await checkPortAvailable(pythonPort);
    if (!portCheck.available) {
      console.error('Port not available:', portCheck.error);
      pythonBackendStatus = 'failed';
      pythonBackendError = portCheck.error;

      if (mainWindow) {
        dialog.showMessageBox(mainWindow, {
          type: 'warning',
          title: 'Port Already In Use',
          message: `Port ${pythonPort} is already in use`,
          detail:
            'Another application is using the port needed by the Python backend.\n\n' +
            'This could be:\n' +
            '- Another instance of this application\n' +
            '- A development server running on the same port\n' +
            '- Another application using port 8000\n\n' +
            'Please close the other application and restart Modelling Mate.',
          buttons: ['OK']
        });
      }

      resolve();
      return;
    }

    // Try to find bundled Python backend first (PREFERRED - no Python install needed!)
    let bundledBackendPath;
    if (isDev) {
      bundledBackendPath = path.join(__dirname, '../backend/dist/modelling-mate-backend/modelling-mate-backend.exe');
    } else {
      // In production, try multiple possible locations
      const appPath = app.getAppPath();
      const possiblePaths = [
        path.join(appPath + '.unpacked', 'backend', 'dist', 'modelling-mate-backend', 'modelling-mate-backend.exe'),
        path.join(path.dirname(appPath), 'app.asar.unpacked', 'backend', 'dist', 'modelling-mate-backend', 'modelling-mate-backend.exe'),
        path.join(process.resourcesPath, 'app.asar.unpacked', 'backend', 'dist', 'modelling-mate-backend', 'modelling-mate-backend.exe'),
      ];

      // Try each possible path
      for (const testPath of possiblePaths) {
        console.log('Checking path:', testPath);
        if (fs.existsSync(testPath)) {
          bundledBackendPath = testPath;
          break;
        }
      }

      // If not found, use first path as default (for error messages)
      if (!bundledBackendPath) {
        bundledBackendPath = possiblePaths[0];
      }
    }

    const useBundledBackend = fs.existsSync(bundledBackendPath);
    console.log('Bundled backend check:', useBundledBackend ? 'FOUND ✓' : 'NOT FOUND');
    if (useBundledBackend) {
      console.log('Bundled backend path:', bundledBackendPath);
    } else {
      console.log('Bundled backend NOT found. Checked paths:');
      if (!isDev) {
        const appPath = app.getAppPath();
        console.log('  -', path.join(appPath + '.unpacked', 'backend', 'dist', 'modelling-mate-backend', 'modelling-mate-backend.exe'));
        console.log('  -', path.join(path.dirname(appPath), 'app.asar.unpacked', 'backend', 'dist', 'modelling-mate-backend', 'modelling-mate-backend.exe'));
        console.log('  -', path.join(process.resourcesPath, 'app.asar.unpacked', 'backend', 'dist', 'modelling-mate-backend', 'modelling-mate-backend.exe'));
      }
    }

    let pythonExe, pythonArgs, workingDir, pythonVersion;

    if (useBundledBackend) {
      // Use bundled Python backend (no Python installation required!)
      console.log('Using BUNDLED Python backend (self-contained)');
      pythonExe = bundledBackendPath;
      pythonArgs = [];  // No arguments needed - executable handles everything
      workingDir = path.dirname(bundledBackendPath);
      pythonVersion = 'Bundled (self-contained)';

      // Verify the working directory exists
      if (!fs.existsSync(workingDir)) {
        console.error('ERROR: Bundled backend directory does not exist:', workingDir);
        pythonBackendStatus = 'failed';
        pythonBackendError = `Backend directory not found: ${workingDir}`;
        resolve();
        return;
      }

      // Log directory contents for debugging
      console.log('Working directory:', workingDir);
      console.log('Directory contents:', fs.readdirSync(workingDir).join(', '));
    } else {
      // Fallback to system Python (requires Python installation)
      console.log('Bundled backend not found, checking for system Python...');

      const pythonCheck = await checkPythonInstalled();
      if (!pythonCheck.installed) {
        console.error('Python not installed:', pythonCheck.error);
        pythonBackendStatus = 'failed';
        pythonBackendError = pythonCheck.error;

        if (mainWindow) {
          const installScriptPath = path.join(scriptsDir, 'Install-Dependencies.bat');
          const scriptExists = fs.existsSync(installScriptPath);

          dialog.showMessageBox(mainWindow, {
            type: 'error',
            title: 'Python Backend Not Available',
            message: 'Neither bundled backend nor system Python found',
            detail:
              'The application was built without the bundled Python backend.\n\n' +
              'Fallback option - Install Python:\n' +
              '1. Install Python 3.9-3.11 from python.org\n' +
              '2. Check "Add Python to PATH" during installation\n' +
              '3. Run Install-Dependencies.bat as Administrator\n' +
              '4. Restart this application\n\n' +
              'Or contact support for a version with bundled Python.\n\n' +
              `Technical error: ${pythonCheck.error}`,
            buttons: scriptExists ? ['Open Scripts Folder', 'OK'] : ['OK'],
            defaultId: scriptExists ? 0 : 0,
            cancelId: scriptExists ? 1 : 0,
          }).then((result) => {
            if (result.response === 0 && scriptExists) {
              const { shell } = require('electron');
              shell.openPath(path.dirname(installScriptPath));
            }
          });
        }

        resolve();
        return;
      }

      // System Python found - use it
      console.log('Using SYSTEM Python (requires dependencies)');
      pythonExe = process.platform === 'win32' ? 'python' : 'python3';
      pythonArgs = [pythonScript];
      workingDir = pythonDir;
      pythonVersion = pythonCheck.version;
    }

    // Start the backend (either bundled or system Python)
    console.log('='.repeat(50));
    console.log('Backend Configuration:');
    console.log('  Type:', useBundledBackend ? 'BUNDLED (self-contained)' : 'SYSTEM (requires Python)');
    console.log('  Executable:', pythonExe);
    console.log('  Arguments:', pythonArgs.length > 0 ? pythonArgs : '(none)');
    console.log('  Working Dir:', workingDir);
    console.log('  Python Version:', pythonVersion);
    console.log('  Port:', pythonPort);
    console.log('='.repeat(50));

    const spawnOptions = {
      cwd: workingDir,
      shell: process.platform === 'win32' ? 'cmd.exe' : true,
    };

    pythonBackend = spawn(pythonExe, pythonArgs, spawnOptions);

    let backendOutput = '';
    let backendErrors = '';

    pythonBackend.stdout.on('data', (data) => {
      const output = data.toString();
      backendOutput += output;
      console.log(`Python Backend: ${output}`);

      // Check if backend has started successfully
      if (output.includes('Uvicorn running') || output.includes('Application startup complete')) {
        console.log('Python backend startup detected in output');
      }
    });

    pythonBackend.stderr.on('data', (data) => {
      const error = data.toString();
      backendErrors += error;
      console.error(`Python Backend Error: ${error}`);

      // Check for common errors
      if (error.includes('ModuleNotFoundError') || error.includes('No module named')) {
        console.error('Missing Python module detected');
        pythonBackendError = 'Missing required Python packages. Please run Install-Dependencies.bat';
      } else if (error.includes('Address already in use') || error.includes('EADDRINUSE')) {
        console.error('Port already in use');
        pythonBackendError = `Port ${pythonPort} is already in use`;
      } else if (error.includes('prophet')) {
        console.error('Prophet-related error detected');
        pythonBackendError = 'Prophet library error. May need to reinstall dependencies.';
      }
    });

    pythonBackend.on('error', (error) => {
      console.error('Failed to spawn Python backend process:', error);
      pythonBackendStatus = 'failed';
      pythonBackendError = error.message;

      if (mainWindow) {
        const installScriptPath = path.join(scriptsDir, 'Install-Dependencies.bat');
        const scriptExists = fs.existsSync(installScriptPath);

        dialog.showMessageBox(mainWindow, {
          type: 'error',
          title: 'Python Backend Error',
          message: 'Failed to start the Python backend process',
          detail:
            'An error occurred while trying to start the Python backend.\n\n' +
            'Please make sure:\n' +
            '1. Python 3.9-3.11 is installed\n' +
            '2. Python is added to your PATH\n' +
            '3. Required packages are installed\n\n' +
            `Technical error: ${error.message}`,
          buttons: scriptExists ? ['Run Dependency Installer', 'OK'] : ['OK'],
          defaultId: 0,
          cancelId: scriptExists ? 1 : 0,
        }).then((result) => {
          if (result.response === 0 && scriptExists) {
            const { shell } = require('electron');
            shell.openPath(installScriptPath);
          }
        });
      }
    });

    pythonBackend.on('close', (code) => {
      console.log(`Python backend exited with code ${code}`);

      if (code !== 0 && code !== null) {
        console.error('Python backend crashed');
        console.error('Last output:', backendOutput);
        console.error('Last errors:', backendErrors);

        pythonBackendStatus = 'failed';

        if (!pythonBackendError) {
          pythonBackendError = `Backend exited with code ${code}. Check logs for details.`;
        }

        // Show error if window is available and we haven't shown too many dialogs
        if (mainWindow && pythonBackendStartAttempts === 1) {
          dialog.showMessageBox(mainWindow, {
            type: 'error',
            title: 'Python Backend Crashed',
            message: 'The Python backend stopped unexpectedly',
            detail:
              `The backend process exited with code ${code}.\n\n` +
              'Common causes:\n' +
              '- Missing or incompatible Python packages\n' +
              '- Python version incompatibility (requires 3.9-3.11)\n' +
              '- Corrupted installation\n\n' +
              'Try running Install-Dependencies.bat as Administrator.\n\n' +
              `Technical error: ${pythonBackendError || 'Check console for details'}`,
            buttons: ['OK']
          });
        }
      } else {
        pythonBackendStatus = 'stopped';
      }
    });

    // Wait for backend to be ready with health checks
    let healthCheckAttempts = 0;
    const MAX_HEALTH_CHECKS = 30; // 30 seconds

    const checkBackend = setInterval(async () => {
      healthCheckAttempts++;

      try {
        const http = require('http');
        http.get(`http://localhost:${pythonPort}/health`, (res) => {
          if (res.statusCode === 200) {
            console.log(`Python backend is ready! (took ${healthCheckAttempts} seconds)`);
            pythonBackendStatus = 'running';
            pythonBackendError = null;
            clearInterval(checkBackend);
            resolve();
          }
        }).on('error', (err) => {
          // Backend not ready yet, keep checking
          if (healthCheckAttempts >= MAX_HEALTH_CHECKS) {
            console.error('Health check failed:', err.message);
          }
        });
      } catch (error) {
        // Backend not ready yet
      }

      // Check if we've exceeded max attempts
      if (healthCheckAttempts >= MAX_HEALTH_CHECKS) {
        clearInterval(checkBackend);
        console.warn(`Python backend did not respond to health checks after ${MAX_HEALTH_CHECKS} seconds`);

        pythonBackendStatus = 'failed';
        if (!pythonBackendError) {
          pythonBackendError = 'Backend started but did not respond to health checks';
        }

        console.warn('Backend output:', backendOutput);
        console.warn('Backend errors:', backendErrors);

        // Show a more informative error to the user
        if (mainWindow && pythonBackendStartAttempts === 1) {
          const installScriptPath = path.join(scriptsDir, 'Install-Dependencies.bat');
          const scriptExists = fs.existsSync(installScriptPath);

          dialog.showMessageBox(mainWindow, {
            type: 'warning',
            title: 'Python Backend Not Responding',
            message: 'The Python backend started but is not responding',
            detail:
              'The backend process started but failed to respond to health checks.\n\n' +
              'This usually means:\n' +
              '- Required Python packages are not installed\n' +
              '- Prophet or other dependencies have errors\n' +
              '- Python version is incompatible (requires 3.9-3.11)\n\n' +
              'Please run Install-Dependencies.bat as Administrator.\n\n' +
              `Technical error: ${pythonBackendError}`,
            buttons: scriptExists ? ['Open Scripts Folder', 'Continue Without Backend'] : ['Continue Without Backend'],
            defaultId: 0,
          }).then((result) => {
            if (result.response === 0 && scriptExists) {
              const { shell } = require('electron');
              shell.openPath(path.dirname(installScriptPath));
            }
          });
        }

        resolve();
      }
    }, 1000); // Check every second
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
          label: 'Backend Status',
          click: () => {
            const statusMessage = pythonBackendStatus === 'running'
              ? 'Python backend is running successfully'
              : pythonBackendStatus === 'starting'
              ? 'Python backend is starting...'
              : pythonBackendStatus === 'failed'
              ? `Python backend failed to start: ${pythonBackendError || 'Unknown error'}`
              : 'Python backend not started';

            dialog.showMessageBox(mainWindow, {
              type: pythonBackendStatus === 'running' ? 'info' : 'warning',
              title: 'Backend Status',
              message: statusMessage,
              detail: pythonBackendStatus === 'running'
                ? `Running on port ${pythonPort}\nAttempts: ${pythonBackendStartAttempts}`
                : pythonBackendStatus === 'failed'
                ? 'The app includes a bundled Python backend. If you see this error, please restart the application.'
                : 'Backend is initializing...',
            });
          },
        },
        {
          label: 'Restart Backend',
          click: async () => {
            const result = await dialog.showMessageBox(mainWindow, {
              type: 'question',
              title: 'Restart Backend',
              message: 'Are you sure you want to restart the Python backend?',
              detail: 'This will temporarily interrupt Prophet forecasting and other Python features.',
              buttons: ['Restart', 'Cancel'],
              defaultId: 1,
            });

            if (result.response === 0) {
              // Kill existing backend
              if (pythonBackend) {
                pythonBackend.kill();
              }
              pythonBackendStatus = 'not_started';
              pythonBackendError = null;
              pythonBackendStartAttempts = 0;

              // Restart
              await startPythonBackend();

              dialog.showMessageBox(mainWindow, {
                type: 'info',
                title: 'Backend Restarted',
                message: 'Python backend has been restarted',
                detail: `Status: ${pythonBackendStatus}`,
              });
            }
          },
        },
        { type: 'separator' },
        {
          label: 'Clear Application Cache',
          click: async () => {
            const result = await dialog.showMessageBox(mainWindow, {
              type: 'question',
              title: 'Clear Cache',
              message: 'Clear application cache and data?',
              detail: 'This will clear cached data and require reloading datasets. Your files will not be affected.',
              buttons: ['Clear Cache', 'Cancel'],
              defaultId: 1,
            });

            if (result.response === 0) {
              const { session } = require('electron');
              await session.defaultSession.clearCache();
              await session.defaultSession.clearStorageData();

              dialog.showMessageBox(mainWindow, {
                type: 'info',
                title: 'Cache Cleared',
                message: 'Application cache has been cleared',
                detail: 'Please reload the application for changes to take effect.',
                buttons: ['Reload Now', 'Later'],
              }).then((result) => {
                if (result.response === 0) {
                  mainWindow.reload();
                }
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
        {
          label: 'Open User Data Folder',
          click: () => {
            const { shell } = require('electron');
            shell.openPath(app.getPath('userData'));
          },
        },
        { type: 'separator' },
        {
          label: 'View Log File',
          click: () => {
            const { shell } = require('electron');
            // Check if log file exists
            if (fs.existsSync(logFilePath)) {
              shell.openPath(logFilePath);
            } else {
              dialog.showMessageBox(mainWindow, {
                type: 'info',
                title: 'Log File',
                message: 'Log file not found',
                detail: `Expected location: ${logFilePath}\n\nThe log file is created when the app starts.`,
                buttons: ['OK']
              });
            }
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
ipcMain.handle('python:getStatus', async () => {
  return {
    status: pythonBackendStatus,
    error: pythonBackendError,
    attempts: pythonBackendStartAttempts,
    port: pythonPort
  };
});

ipcMain.handle('python:restart', async () => {
  console.log('Restarting Python backend via IPC...');

  // Kill existing backend if running
  if (pythonBackend) {
    try {
      pythonBackend.kill();
      console.log('Killed existing Python backend process');
    } catch (error) {
      console.error('Error killing Python backend:', error);
    }
  }

  // Reset status
  pythonBackendStatus = 'not_started';
  pythonBackendError = null;
  pythonBackendStartAttempts = 0;

  // Start backend again
  await startPythonBackend();

  return {
    status: pythonBackendStatus,
    error: pythonBackendError
  };
});

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
  console.log('Application shutting down...');
  if (pythonBackend) {
    console.log('Stopping Python backend...');
    pythonBackend.kill();
  }
  // Close log stream
  if (logStream) {
    logStream.end();
  }
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
});

process.on('unhandledRejection', (error) => {
  console.error('Unhandled Rejection:', error);
});
