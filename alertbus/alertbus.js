const WebSocket = require('ws');

// Configuration
const FUSION_WS = process.env.FUSION_WS || 'ws://fusion:8770';
const PORT = 8780;

// Create WebSocket server
const wss = new WebSocket.Server({ port: PORT });
console.log(`🚌 Alert Bus listening on port ${PORT}`);

// Connected clients
const clients = new Set();

// Connect to fusion service
function connectToFusion() {
  console.log(`Connecting to fusion service at ${FUSION_WS}...`);
  const fusionWs = new WebSocket(FUSION_WS);

  fusionWs.on('open', () => {
    console.log('Connected to fusion service');
  });

  fusionWs.on('message', (data) => {
    try {
      const alert = JSON.parse(data.toString());
      console.log(`Received alert: ${alert.event}`);
      
      // Broadcast to all connected clients
      clients.forEach((client) => {
        if (client.readyState === WebSocket.OPEN) {
          client.send(data.toString());
        }
      });
    } catch (err) {
      console.error('Error processing message:', err);
    }
  });

  fusionWs.on('close', () => {
    console.log('Disconnected from fusion service, reconnecting in 5s...');
    setTimeout(connectToFusion, 5000);
  });

  fusionWs.on('error', (err) => {
    console.error('Fusion WebSocket error:', err);
    fusionWs.close();
  });
}

// Handle client connections
wss.on('connection', (ws) => {
  console.log('Client connected');
  clients.add(ws);

  ws.on('close', () => {
    console.log('Client disconnected');
    clients.delete(ws);
  });
});

// Start connection to fusion
connectToFusion();
