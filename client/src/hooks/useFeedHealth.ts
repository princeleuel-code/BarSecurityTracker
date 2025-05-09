import { useState, useEffect } from 'react';
import { wsClient } from '@/lib/websocket';

interface FeedMetrics {
  bitrate: number;
  fps: number;
  timestamp: number;
}

interface UseFeedHealthReturn {
  status: 'online' | 'offline' | 'error';
  bitrate: number;
  fps: number;
  lastUpdate: Date | null;
  history: FeedMetrics[];
}

export function useFeedHealth(feedId: string): UseFeedHealthReturn {
  const [status, setStatus] = useState<'online' | 'offline' | 'error'>('offline');
  const [bitrate, setBitrate] = useState(0);
  const [fps, setFps] = useState(0);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [history, setHistory] = useState<FeedMetrics[]>([]);

  useEffect(() => {
    let staleTimeout: NodeJS.Timeout;

    console.log(`useFeedHealth hook initialized for feed: ${feedId}, current status: ${status}`);

    const handleMessage = (message: any) => {
      console.log('Received message in useFeedHealth:', message);

      // Handle feed status messages (lowercase from server)
      if (message.type === 'feed-status' && message.data && message.data.feedId === feedId) {
        console.log(`Setting status to: ${message.data.status} for feed: ${feedId}`);
        setStatus(message.data.status);
        setLastUpdate(new Date());

        // Reset stale timer
        if (staleTimeout) clearTimeout(staleTimeout);
        staleTimeout = setTimeout(() => {
          console.log(`Stale timeout triggered, setting status to offline for feed: ${feedId}`);
          setStatus('offline');
          setBitrate(0);
          setFps(0);
        }, 5000); // Mark as stale after 5 seconds without updates
      }

      // Handle feed metrics messages
      if (message.type === 'feed-metrics' && message.data && message.data.feedId === feedId) {
        setBitrate(message.data.bitrate || 0);
        setFps(message.data.fps || 0);
        setLastUpdate(new Date());

        // Add to history
        setHistory(prev => {
          const newMetrics = {
            bitrate: message.data.bitrate || 0,
            fps: message.data.fps || 0,
            timestamp: Date.now()
          };
          // Keep last 60 data points (1 minute at 1 update/sec)
          const newHistory = [...prev, newMetrics].slice(-60);
          return newHistory;
        });
      }

      // Handle error events
      if (message.type === 'feed-error' && message.data && message.data.feedId === feedId) {
        setStatus('error');
        setBitrate(0);
        setFps(0);
      }
    };

    // Subscribe to feed status updates
    wsClient.addMessageHandler(handleMessage);

    // We don't need to request status or metrics as the server
    // is already broadcasting them automatically

    // For debugging, log connection status
    console.log('WebSocket connected:', wsClient.isConnected());

    return () => {
      if (staleTimeout) clearTimeout(staleTimeout);
      wsClient.removeMessageHandler(handleMessage);
    };
  }, [feedId]);

  return {
    status,
    bitrate,
    fps,
    lastUpdate,
    history
  };
}