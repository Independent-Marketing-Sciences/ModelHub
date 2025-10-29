const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electron', {
  // File operations
  openFile: () => ipcRenderer.invoke('dialog:openFile'),
  readFile: (filePath) => ipcRenderer.invoke('file:read', filePath),
  saveFile: (data) => ipcRenderer.invoke('dialog:saveFile', data),

  // App info
  getAppVersion: () => ipcRenderer.invoke('app:getVersion'),

  // Generic IPC invoke for additional features
  invoke: (channel, ...args) => ipcRenderer.invoke(channel, ...args),

  // Future: Add more secure APIs as needed
});
