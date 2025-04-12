import { useEffect, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Alert } from '@shared/schema';
import { Card, CardHeader, CardContent, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { BellRing, CheckCircle } from 'lucide-react';
import { wsClient } from '@/lib/websocket';
import { apiRequest } from '@/lib/queryClient';

export function AlertPanel() {
  const queryClient = useQueryClient();
  const [newAlerts, setNewAlerts] = useState<Alert[]>([]);

  const { data: alerts = [] } = useQuery<Alert[]>({ 
    queryKey: ['/api/alerts']
  });

  useEffect(() => {
    const handleMessage = (message: any) => {
      if (message.type === 'ALERT') {
        setNewAlerts(prev => [message.data, ...prev]);
      }
    };

    wsClient.addMessageHandler(handleMessage);
    return () => wsClient.removeMessageHandler(handleMessage);
  }, []);

  const acknowledgeAlert = async (id: number) => {
    await apiRequest('POST', `/api/alerts/${id}/acknowledge`);
    queryClient.invalidateQueries({ queryKey: ['/api/alerts'] });
    setNewAlerts(prev => prev.filter(alert => alert.id !== id));
  };

  const allAlerts = [...newAlerts, ...alerts];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BellRing className="h-5 w-5" />
          Security Alerts
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 max-h-[400px] overflow-y-auto">
        {allAlerts.map(alert => (
          <div
            key={alert.id}
            className={`p-4 rounded-lg flex items-center justify-between ${
              alert.level === 'WARNING' ? 'bg-yellow-100' : 'bg-red-100'
            }`}
          >
            <div>
              <p className="font-medium">{alert.message}</p>
              <p className="text-sm text-gray-600">
                {new Date(alert.timestamp).toLocaleString()}
              </p>
            </div>
            {!alert.acknowledged && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => acknowledgeAlert(alert.id)}
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                Acknowledge
              </Button>
            )}
          </div>
        ))}
        {allAlerts.length === 0 && (
          <p className="text-center text-gray-500">No alerts</p>
        )}
      </CardContent>
    </Card>
  );
}
