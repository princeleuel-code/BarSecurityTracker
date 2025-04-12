import { useEffect } from 'react';
import { VideoFeed } from '@/components/video-feed';
import { AlertPanel } from '@/components/alert-panel';
import { EventLog } from '@/components/event-log';
import { wsClient } from '@/lib/websocket';

export default function Dashboard() {
  useEffect(() => {
    wsClient.connect();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <header className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900">Bar Security Monitor</h1>
        <p className="text-gray-600">Real-time surveillance and threat detection</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-8">
          <VideoFeed />
          <AlertPanel />
        </div>
        <div>
          <EventLog />
        </div>
      </div>
    </div>
  );
}
