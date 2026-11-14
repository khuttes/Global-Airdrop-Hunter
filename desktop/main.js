require('../patch-electron.js');
const { app, BrowserWindow, ipcMain, shell, protocol } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const crypto = require('crypto');

let mainWindow = null;
let backendProcess = null;
let apiToken = null;
let backendPort = 8000;

function generateToken() {
  return crypto.randomBytes(32).toString('hex');
}

function getBackendPath() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'backend');
  }
  return path.join(__dirname, '..');
}

function getPythonExecutable() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, '.venv', 'Scripts', 'python.exe');
  }
  return path.join(__dirname, '..', '.venv', 'Scripts', 'python.exe');
}

function startBackend() {
  return new Promise((resolve, reject) => {
    const backendDir = getBackendPath();
    const pythonExe = getPythonExecutable();
    const mainPy = path.join(backendDir, 'backend', 'main.py');

    if (!fs.existsSync(pythonExe)) {
      reject(new Error(`Python executable not found at ${pythonExe}`));
      return;
    }
    if (!fs.existsSync(mainPy)) {
      reject(new Error(`Backend main.py not found at ${mainPy}`));
      return;
    }

    apiToken = generateToken();
    const env = {
      ...process.env,
      PYTHONPATH: backendDir,
      LOCAL_API_TOKEN: apiToken,
      BACKEND_PORT: backendPort.toString(),
      APP_DATA_DIR: path.join(app.getPath('userData'), 'GlobalAirdropHunter'),
    };

    backendProcess = spawn(pythonExe, ['-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', backendPort.toString()], {
      cwd: backendDir,
      env,
      windowsHide: true,
    });

    backendProcess.stdout.on('data', (data) => {
      console.log(`[Backend] ${data}`);
    });

    backendProcess.stderr.on('data', (data) => {
      console.error(`[Backend Error] ${data}`);
    });

    backendProcess.on('error', (err) => {
      console.error('Failed to start backend:', err);
      reject(err);
    });

    backendProcess.on('exit', (code) => {
      console.log(`Backend exited with code ${code}`);
      backendProcess = null;
    });

    setTimeout(() => {
      checkBackendHealth().then(resolve).catch(reject);
    }, 2000);
  });
}

function checkBackendHealth() {
  return new Promise((resolve, reject) => {
    const http = require('http');
    const options = {
      hostname: '127.0.0.1',
      port: backendPort,
      path: '/api/v1/health',
      method: 'GET',
      headers: {
        'X-Local-API-Token': apiToken,
      },
      timeout: 5000,
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        if (res.statusCode === 200) {
          resolve();
        } else {
          reject(new Error(`Health check failed: ${res.statusCode} ${data}`));
        }
      });
    });

    req.on('error', (err) => reject(err));
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Health check timeout'));
    });
    req.end();
  });
}

function stopBackend() {
  if (backendProcess) {
    backendProcess.kill('SIGTERM');
    backendProcess = null;
  }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1000,
    minHeight: 700,
    title: 'Global Airdrop Hunter',
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: true,
      allowRunningInsecureContent: false,
      experimentalFeatures: false,
      spellcheck: false,
    },
    icon: path.join(__dirname, '..', 'build', 'icon.ico'),
  });

  mainWindow.setMenuBarVisibility(false);

  const csp = [
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data:",
    "font-src 'self'",
    "connect-src 'self' http://127.0.0.1:*",
    "frame-src 'none'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ].join('; ');

  mainWindow.webContents.session.webRequest.onHeadersReceived((details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        'Content-Security-Policy': [csp],
        'X-Content-Type-Options': ['nosniff'],
        'X-Frame-Options': ['DENY'],
        'Referrer-Policy': ['strict-origin-when-cross-origin'],
      },
    });
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http://') || url.startsWith('https://')) {
      shell.openExternal(url);
    }
    return { action: 'deny' };
  });

  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (!url.startsWith('file://') && !url.startsWith('http://127.0.0.1:') && !url.startsWith('https://127.0.0.1:')) {
      event.preventDefault();
      if (url.startsWith('http://') || url.startsWith('https://')) {
        shell.openExternal(url);
      }
    }
  });

  if (process.argv.includes('--dev')) {
    mainWindow.loadFile(path.join(__dirname, '..', 'frontend', 'index.html')).catch(console.error);
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'frontend', 'index.html')).catch(console.error);
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.on('ready', async () => {
  try {
    await startBackend();
    createWindow();
  } catch (err) {
    console.error('Failed to start application:', err);
    app.quit();
  }
});

app.on('window-all-closed', () => {
  stopBackend();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

app.on('before-quit', () => {
  stopBackend();
});

ipcMain.handle('get-api-config', () => {
  return {
    baseUrl: `http://127.0.0.1:${backendPort}`,
    token: apiToken,
  };
});

ipcMain.handle('open-external', (event, url) => {
  if (typeof url === 'string' && (url.startsWith('http://') || url.startsWith('https://'))) {
    try {
      new URL(url);
      return shell.openExternal(url);
    } catch {
      return { success: false, error: 'Invalid URL' };
    }
  }
  return { success: false, error: 'Invalid URL scheme' };
});

ipcMain.handle('get-app-version', () => {
  return app.getVersion();
});