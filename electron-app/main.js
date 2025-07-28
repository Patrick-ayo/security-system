const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

let mainWindow;
let pythonProcess;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'assets', 'icon.png'),
    title: 'AI Security Monitor'
  });

  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));

  // Open DevTools in development
  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }
}

function startPythonBackend() {
  // Try the simplified backend first, fall back to full backend
  const simplePythonPath = path.join(__dirname, '..', 'python-backend', 'app_simple.py');
  const fullPythonPath = path.join(__dirname, '..', 'python-backend', 'app.py');
  
  // Check if simplified backend exists
  if (fs.existsSync(simplePythonPath)) {
    pythonProcess = spawn('python', [simplePythonPath], {
      stdio: ['pipe', 'pipe', 'pipe']
    });
    console.log('Using simplified Python backend');
  } else {
    pythonProcess = spawn('python', [fullPythonPath], {
      stdio: ['pipe', 'pipe', 'pipe']
    });
    console.log('Using full Python backend');
  }

  pythonProcess.stdout.on('data', (data) => {
    console.log('Python Backend:', data.toString());
    mainWindow.webContents.send('python-log', data.toString());
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error('Python Backend Error:', data.toString());
    mainWindow.webContents.send('python-error', data.toString());
  });

  pythonProcess.on('close', (code) => {
    console.log(`Python process exited with code ${code}`);
    mainWindow.webContents.send('python-closed', code);
  });
}

// IPC Handlers
ipcMain.handle('start-monitoring', async () => {
  try {
    mainWindow.webContents.send('python-command', 'start_monitoring');
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('stop-monitoring', async () => {
  try {
    mainWindow.webContents.send('python-command', 'stop_monitoring');
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('get-incidents', async () => {
  try {
    const incidentsPath = path.join(__dirname, '..', 'python-backend', 'data', 'incidents.json');
    if (fs.existsSync(incidentsPath)) {
      const data = fs.readFileSync(incidentsPath, 'utf8');
      return JSON.parse(data);
    }
    return [];
  } catch (error) {
    return { error: error.message };
  }
});

ipcMain.handle('select-directory', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory']
  });
  return result.filePaths[0] || null;
});

ipcMain.handle('get-config', async () => {
  try {
    const configPath = path.join(__dirname, '..', 'shared', 'config.json');
    const data = fs.readFileSync(configPath, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    return { error: error.message };
  }
});

ipcMain.handle('save-config', async (event, config) => {
  try {
    const configPath = path.join(__dirname, '..', 'shared', 'config.json');
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

app.whenReady().then(() => {
  createWindow();
  startPythonBackend();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
});

// Handle Python process communication
process.on('message', (message) => {
  if (mainWindow) {
    mainWindow.webContents.send('python-message', message);
  }
}); 