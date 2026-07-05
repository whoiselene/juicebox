const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  /**
   * Sends a command JSON object to the Python daemon.
   */
  send: (message) => {
    ipcRenderer.send('to-python', message);
  },
  
  /**
   * Listens for event/response messages from the Python daemon.
   * Callback signature: (data) => void
   */
  onReceive: (callback) => {
    ipcRenderer.on('from-python', (event, data) => callback(data));
  }
});
