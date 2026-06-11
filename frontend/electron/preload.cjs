const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('irisflow', {
  onBackendReady: (cb) => ipcRenderer.on('backend-ready', cb),
  send: (channel, data) => ipcRenderer.send(channel, data),
})
