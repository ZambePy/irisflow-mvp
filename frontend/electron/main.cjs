const { app, BrowserWindow, Menu } = require('electron')
const path = require('path')
const { spawn } = require('child_process')
const fs = require('fs')

let mainWindow = null
let backend = null

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 1024,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:5173')
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'))
  }

  mainWindow.on('closed', () => {
    mainWindow = null
    if (backend) backend.kill()
  })
}

function startBackend() {
  const repoRoot = path.join(__dirname, '../../')
  const venvPython = process.platform === 'win32'
    ? path.join(repoRoot, '.venv', 'Scripts', 'python.exe')
    : path.join(repoRoot, '.venv', 'bin', 'python')
  const pythonCmd = process.env.IRISFLOW_PYTHON || (fs.existsSync(venvPython) ? venvPython : 'python')

  backend = spawn(pythonCmd, ['-m', 'irisflow.api.main'], {
    cwd: repoRoot,
    env: { ...process.env },
  })

  backend.stdout.on('data', (data) => {
    console.log('[backend]', data.toString())
    if (mainWindow && data.toString().includes('ready')) {
      mainWindow.webContents.send('backend-ready')
    }
  })

  backend.stderr.on('data', (data) => {
    console.error('[backend err]', data.toString())
  })
}

function buildMenu() {
  const template = [
    {
      label: 'File',
      submenu: [{ label: 'Quit', accelerator: 'CmdOrCtrl+Q', click: () => app.quit() }],
    },
  ]
  Menu.setApplicationMenu(Menu.buildFromTemplate(template))
}

app.whenReady().then(() => {
  buildMenu()
  startBackend()
  createWindow()
})

app.on('window-all-closed', () => {
  if (backend) backend.kill()
  if (process.platform !== 'darwin') app.quit()
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow()
})
