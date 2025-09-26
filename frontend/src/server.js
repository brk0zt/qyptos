// Example WebSocket server (server.js)
const WebSocket = require('ws');
const wss = new WebSocket.Server({
    port: 3000,
    // Add CORS if needed
    perMessageDeflate: false
});

wss.on('connection', (ws) => {
    console.log('Client connected');
    ws.on('message', (message) => {
        console.log('Received:', message);
    });
});
