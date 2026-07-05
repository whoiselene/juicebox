const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

// Load environment variables from .env
require('dotenv').config();

let mainWindow = null;
let pythonProcess = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1100,
    height: 750,
    minWidth: 900,
    minHeight: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    },
    // Stylized frame settings can go here if needed, but a standard frame is best for window controls
    title: "JuiceBox // Project Papaya",
    icon: path.join(__dirname, 'icon.png') // Optional placeholder
  });

  mainWindow.loadFile('index.html');

  // Open DevTools if running in debug (optional)
  // mainWindow.webContents.openDevTools();

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startPythonDaemon() {
  // Determine path to python in the venv
  let pythonPath = path.join(__dirname, 'backend', 'venv', 'bin', 'python');
  
  // Windows compatibility just in case
  if (process.platform === 'win32') {
    pythonPath = path.join(__dirname, 'backend', 'venv', 'Scripts', 'python.exe');
  }

  // Fallback to global python3 if venv python doesn't exist
  if (!fs.existsSync(pythonPath)) {
    console.warn(`Python venv not found at ${pythonPath}. Falling back to system python3.`);
    pythonPath = 'python3';
  }

  const scriptPath = path.join(__dirname, 'backend', 'daemon.py');

  console.log(`Spawning Python process: ${pythonPath} ${scriptPath}`);
  
  // Pass current environment variables to python child process
  const env = { ...process.env };
  
  pythonProcess = spawn(pythonPath, [scriptPath], { env });

  let buffer = '';

  pythonProcess.stdout.on('data', (data) => {
    buffer += data.toString();
    let lines = buffer.split('\n');
    buffer = lines.pop(); // Keep remaining incomplete line in buffer

    for (let line of lines) {
      if (line.trim()) {
        try {
          const parsed = JSON.parse(line);
          console.log("Daemon event received:", parsed.type);
          if (mainWindow) {
            mainWindow.webContents.send('from-python', parsed);
          }
        } catch (err) {
          console.error("Failed to parse JSON from Python daemon:", line, err);
        }
      }
    }
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python Daemon stderr: ${data}`);
  });

  pythonProcess.on('close', (code) => {
    console.log(`Python Daemon exited with code ${code}`);
    pythonProcess = null;
  });

  pythonProcess.on('error', (err) => {
    console.error(`Failed to start Python Daemon: ${err}`);
  });
}

// IPC channel from Renderer to Python
ipcMain.on('to-python', (event, message) => {
  if (pythonProcess && pythonProcess.stdin) {
    try {
      const jsonStr = JSON.stringify(message) + '\n';
      pythonProcess.stdin.write(jsonStr);
    } catch (err) {
      console.error("Error writing to Python daemon stdin:", err);
    }
  } else {
    console.error("Python daemon not running. Cannot send message:", message);
    if (mainWindow) {
      mainWindow.webContents.send('from-python', {
        type: "error",
        message: "Python background process is not running."
      });
    }
  }
});

app.whenReady().then(() => {
  startPythonDaemon();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// Quit when all windows are closed, except on macOS (standard behavior)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Kill Python process on exit
app.on('will-quit', () => {
  if (pythonProcess) {
    console.log("Terminating Python daemon...");
    pythonProcess.kill();
  }
});
