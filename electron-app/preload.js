const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  startMonitoring: () => ipcRenderer.invoke('start-monitoring'),
  stopMonitoring: () => ipcRenderer.invoke('stop-monitoring'),
  getIncidents: () => ipcRenderer.invoke('get-incidents'),
  selectDirectory: () => ipcRenderer.invoke('select-directory'),
  getConfig: () => ipcRenderer.invoke('get-config'),
  saveConfig: (config) => ipcRenderer.invoke('save-config', config),
  
  // Listeners for Python backend communication
  onPythonLog: (callback) => ipcRenderer.on('python-log', callback),
  onPythonError: (callback) => ipcRenderer.on('python-error', callback),
  onPythonClosed: (callback) => ipcRenderer.on('python-closed', callback),
  onPythonMessage: (callback) => ipcRenderer.on('python-message', callback),
  onPythonCommand: (callback) => ipcRenderer.on('python-command', callback),
  
  // Remove listeners
  removeAllListeners: (channel) => ipcRenderer.removeAllListeners(channel)
}); 