import { useEffect, useRef } from 'react';
import Hls from 'hls.js';
import { Card, CardContent } from '@/components/ui/card';

export function VideoFeed() {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (videoRef.current && Hls.isSupported()) {
      const hls = new Hls();
      hls.loadSource('/hls/playlist.m3u8');
      hls.attachMedia(videoRef.current);
    }
  }, []);

  return (
    <Card className="w-full">
      <CardContent className="p-4">
        <video 
          ref={videoRef}
          controls
          autoPlay
          className="w-full aspect-video bg-black rounded-lg"
        />
      </CardContent>
    </Card>
  );
}
