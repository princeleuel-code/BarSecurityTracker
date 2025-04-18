import { storage } from './storage';

// Simulated YOLO detection results for demo
const DEMO_OBJECTS = ['person', 'bottle', 'chair', 'cell phone'];

export class ObjectDetector {
  private interval: NodeJS.Timer | null = null;
  private wsClients: Set<WebSocket> = new Set();

  start() {
    this.interval = setInterval(() => this.detect(), 1000);
  }

  stop() {
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
    }
  }

  addClient(ws: WebSocket) {
    this.wsClients.add(ws);
  }

  removeClient(ws: WebSocket) {
    this.wsClients.delete(ws);
  }

  private async detect() {
    // Simulate object detection
    const detectedObjects = DEMO_OBJECTS.filter(() => Math.random() > 0.7);
    
    if (detectedObjects.length > 0) {
      const event = await storage.createEvent({
        type: 'DETECTION',
        description: `Detected: ${detectedObjects.join(', ')}`,
        objects: detectedObjects
      });

      // Check for suspicious patterns
      if (this.isSuspiciousPattern(detectedObjects)) {
        const alert = await storage.createAlert({
          level: 'WARNING',
          message: `Suspicious activity detected: ${detectedObjects.join(', ')}`
        });

        this.notifyClients({
          type: 'ALERT',
          data: alert
        });
      }

      this.notifyClients({
        type: 'DETECTION',
        data: event
      });
    }
  }

  private isSuspiciousPattern(objects: string[]): boolean {
    // Simple example: Flag if person and multiple objects detected together
    return objects.includes('person') && objects.length > 2;
  }

  private notifyClients(message: any) {
    const payload = JSON.stringify(message);
    for (const client of this.wsClients) {
      if (client.readyState === WebSocket.OPEN) {
        client.send(payload);
      }
    }
  }
}

export const objectDetector = new ObjectDetector();
