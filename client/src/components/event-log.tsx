import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Event } from '@shared/schema';
import { Card, CardHeader, CardContent, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Clock } from 'lucide-react';
import { wsClient } from '@/lib/websocket';

export function EventLog() {
  const [newEvents, setNewEvents] = useState<Event[]>([]);
  
  const { data: events = [] } = useQuery<Event[]>({ 
    queryKey: ['/api/events']
  });

  useEffect(() => {
    const handleMessage = (message: any) => {
      if (message.type === 'DETECTION') {
        setNewEvents(prev => [message.data, ...prev]);
      }
    };

    wsClient.addMessageHandler(handleMessage);
    return () => wsClient.removeMessageHandler(handleMessage);
  }, []);

  const allEvents = [...newEvents, ...events];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-5 w-5" />
          Event Log
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[400px]">
          <div className="space-y-4">
            {allEvents.map((event, i) => (
              <div
                key={event.id}
                className="p-4 rounded-lg bg-gray-50"
              >
                <p className="font-medium">{event.description}</p>
                <div className="flex gap-2 mt-2">
                  {event.objects.map((obj, i) => (
                    <span
                      key={i}
                      className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm"
                    >
                      {obj}
                    </span>
                  ))}
                </div>
                <p className="text-sm text-gray-600 mt-2">
                  {new Date(event.timestamp).toLocaleString()}
                </p>
              </div>
            ))}
            {allEvents.length === 0 && (
              <p className="text-center text-gray-500">No events recorded</p>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
