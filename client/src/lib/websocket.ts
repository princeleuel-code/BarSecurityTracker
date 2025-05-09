import { Event, Alert } from '@shared/schema';

type MessageHandler = (message: any) => void;
type ConnectionHandler = () => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private messageHandlers: Set<MessageHandler> = new Set();
  private connectionHandlers: Set<ConnectionHandler> = new Set();
  private disconnectionHandlers: Set<ConnectionHandler> = new Set();
  private reconnectTimeout: number | null = null;
  private isConnecting: boolean = false;
  private shouldReconnect: boolean = true;
  private reconnectAttempts: number = 0;
  private heartbeatInterval: number | null = null;
  private readonly HEARTBEAT_INTERVAL = 30000; // 30 seconds
  private readonly MAX_RECONNECT_DELAY = 30000; // 30 seconds

  constructor() {
    // Start connection when instantiated
    this.connect();
  }

  connect() {
    if (this.isConnecting || this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    this.isConnecting = true;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Connect directly to the metrics WebSocket port
    const wsUrl = `${protocol}//localhost:8790`;

    console.log('Connecting to WebSocket:', wsUrl);
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      this.isConnecting = false;
      this.reconnectAttempts = 0;
      console.log('WebSocket connected to:', wsUrl);

      if (this.reconnectTimeout) {
        clearTimeout(this.reconnectTimeout);
        this.reconnectTimeout = null;
      }

      // Start heartbeat
      this.startHeartbeat();

      // Notify connection handlers
      this.connectionHandlers.forEach(handler => handler());

      // Send a test message to check if the connection is working
      this.send({ type: 'test', data: { message: 'Hello from client' } });
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        // Don't log heartbeat messages
        if (message.type !== 'heartbeat') {
          console.log('WebSocket message received:', message);
        }

        this.messageHandlers.forEach(handler => handler(message));
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onclose = (event) => {
      this.isConnecting = false;
      this.stopHeartbeat();
      console.log('WebSocket disconnected', event.code, event.reason);

      // Notify disconnection handlers
      this.disconnectionHandlers.forEach(handler => handler());

      if (this.shouldReconnect) {
        // Exponential backoff for reconnection attempts
        const timeout = Math.min(1000 * Math.pow(2, this.reconnectAttempts), this.MAX_RECONNECT_DELAY);
        console.log(`Reconnecting in ${timeout}ms (attempt ${this.reconnectAttempts + 1})`);
        this.reconnectTimeout = window.setTimeout(() => {
          this.reconnectAttempts++;
          this.connect();
        }, timeout);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  private startHeartbeat() {
    this.stopHeartbeat(); // Clear any existing interval
    this.heartbeatInterval = window.setInterval(() => {
      this.send({ type: 'heartbeat' });
    }, this.HEARTBEAT_INTERVAL);
  }

  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  disconnect() {
    this.shouldReconnect = false;
    this.stopHeartbeat();

    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.ws) {
      this.ws.close(1000, 'Client disconnecting');
    }
  }

  addMessageHandler(handler: MessageHandler) {
    this.messageHandlers.add(handler);
  }

  removeMessageHandler(handler: MessageHandler) {
    this.messageHandlers.delete(handler);
  }

  addConnectionHandler(handler: ConnectionHandler) {
    this.connectionHandlers.add(handler);
  }

  removeConnectionHandler(handler: ConnectionHandler) {
    this.connectionHandlers.delete(handler);
  }

  addDisconnectionHandler(handler: ConnectionHandler) {
    this.disconnectionHandlers.add(handler);
  }

  removeDisconnectionHandler(handler: ConnectionHandler) {
    this.disconnectionHandlers.delete(handler);
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  send(data: any) {
    if (this.isConnected()) {
      this.ws!.send(JSON.stringify(data));
    } else {
      console.warn('Attempted to send message while disconnected:', data);
    }
  }
}

// Create singleton instance
export const wsClient = new WebSocketClient();
