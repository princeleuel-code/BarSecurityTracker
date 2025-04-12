import type { Express } from "express";
import { createServer, type Server } from "http";
import { WebSocketServer, WebSocket } from 'ws';
import { storage } from "./storage";
import { videoProcessor } from "./video-processor";
import { objectDetector } from "./object-detector";

export function registerRoutes(app: Express): Server {
  const httpServer = createServer(app);
  
  // Initialize WebSocket server
  const wss = new WebSocketServer({ server: httpServer, path: '/ws' });

  // Start video processing and object detection
  videoProcessor.startStreaming();
  objectDetector.start();

  // WebSocket connection handling
  wss.on('connection', (ws: WebSocket) => {
    objectDetector.addClient(ws);

    ws.on('close', () => {
      objectDetector.removeClient(ws);
    });
  });

  // REST API routes
  app.get('/api/events', async (req, res) => {
    const limit = req.query.limit ? parseInt(req.query.limit as string) : undefined;
    const events = await storage.getEvents(limit);
    res.json(events);
  });

  app.get('/api/alerts', async (req, res) => {
    const limit = req.query.limit ? parseInt(req.query.limit as string) : undefined;
    const alerts = await storage.getAlerts(limit);
    res.json(alerts);
  });

  app.post('/api/alerts/:id/acknowledge', async (req, res) => {
    const id = parseInt(req.params.id);
    const alert = await storage.acknowledgeAlert(id);
    if (alert) {
      res.json(alert);
    } else {
      res.status(404).json({ message: 'Alert not found' });
    }
  });

  return httpServer;
}
