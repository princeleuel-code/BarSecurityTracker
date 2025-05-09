import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Event } from '@shared/schema';
import { Card, CardHeader, CardContent, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Clock, WifiOff, Loader2 } from 'lucide-react';
import { wsClient } from '@/lib/websocket';
import { useToast } from '@/components/ui/use-toast';

export function EventLog() {
  const [newEvents, setNewEvents] = useState<Event[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const { toast } = useToast();
  
  const { data: events = [], isLoading, error } = useQuery<Event[]>({
    queryKey: ['/api/events'],
    retry: 3,
    staleTime: 30000, // Consider data fresh for 30 seconds
    onError: (err) => {
      toast({
        title: "Error loading events",
        description: err.message,
        variant: "destructive"
      });
    }
  });

  useEffect(() => {
    const handleMessage = (message: any) => {
      if (message.type === 'DETECTION') {
        setNewEvents(prev => {
          // Prevent duplicate events
          if (prev.some(e => e.id === message.data.id)) {
            return prev;
          }
          return [message.data, ...prev].slice(0, 100); // Keep last 100 events
        });
      }
    };

    const handleConnect = () => {
      setIsConnected(true);
      toast({
        title: "Connected",
        description: "Real-time event updates enabled"
      });
    };

    const handleDisconnect = () => {
      setIsConnected(false);
      // Only show disconnect toast if we were previously connected
      if (isConnected) {
        toast({
          title: "Disconnected",
          description: "Attempting to reconnect...",
          variant: "destructive"
        });
      }
    };

    wsClient.addMessageHandler(handleMessage);
    wsClient.addConnectionHandler(handleConnect);
    wsClient.removeConnectionHandler(handleDisconnect);

    // Check initial connection state
    setIsConnected(wsClient.isConnected());

    return () => {
      wsClient.removeMessageHandler(handleMessage);
      wsClient.removeConnectionHandler(handleConnect);
      wsClient.removeConnectionHandler(handleDisconnect);
    };
  }, [isConnected, toast]);

  const allEvents = [...newEvents, ...events];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Event Log
          </div>
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          ) : !isConnected ? (
            <WifiOff className="h-4 w-4 text-destructive" />
          ) : null}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[400px]">
          {error ? (
            <div className="flex h-full items-center justify-center text-muted-foreground">
              Failed to load events: {error.message}
            </div>
          ) : isLoading && allEvents.length === 0 ? (
            <div className="flex h-full items-center justify-center text-muted-foreground">
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Loading events...
            </div>
          ) : allEvents.length === 0 ? (
            <div className="flex h-full items-center justify-center text-muted-foreground">
              No events to display
            </div>
          ) : (
            <div className="space-y-4">
              {allEvents.map((event) => (
                <div
                  key={event.id}
                  className="rounded-lg border bg-card p-4 text-card-foreground shadow-sm"
                >
                  <div className="mb-2 flex items-center justify-between">
                    <h4 className="font-semibold">{event.type}</h4>
                    <time className="text-sm text-muted-foreground">
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </time>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {event.description}
                  </p>
                  {event.details && (
                    <pre className="mt-2 overflow-auto rounded bg-muted p-2 text-xs">
                      {JSON.stringify(event.details, null, 2)}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
