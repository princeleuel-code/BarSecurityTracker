import { useEffect, useRef, useState } from 'react';
import Hls from 'hls.js';
import { Card, CardContent } from '@/components/ui/card';

export function VideoFeed() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const hlsUrl = import.meta.env.VITE_HLS_URL || 'http://localhost:8888/cam1-hls/stream.m3u8';
    console.log('Loading HLS stream from:', hlsUrl);

    if (videoRef.current && Hls.isSupported()) {
      const hls = new Hls({
        debug: true,
        manifestLoadingMaxRetry: 5,
        manifestLoadingRetryDelay: 1000,
        levelLoadingMaxRetry: 5,
        levelLoadingRetryDelay: 1000,
        maxBufferLength: 10,
        maxMaxBufferLength: 30,
        liveSyncDurationCount: 3,
        liveMaxLatencyDurationCount: 10,
        enableWorker: true
      });

      hls.on(Hls.Events.MEDIA_ATTACHED, () => {
        console.log('HLS.js attached to video element');
      });

      hls.on(Hls.Events.MANIFEST_PARSED, (event, data) => {
        console.log('Manifest loaded, found ' + data.levels.length + ' quality level(s)');
        setLoading(false);
        videoRef.current?.play().catch(e => {
          console.error('Error playing video:', e);
          // Try again with user interaction
          const playPromise = videoRef.current?.play();
          if (playPromise !== undefined) {
            playPromise.catch(() => {
              console.log('Autoplay prevented, waiting for user interaction');
            });
          }
        });
      });

      hls.on(Hls.Events.ERROR, (event, data) => {
        console.error('HLS.js error:', data);
        if (data.fatal) {
          setError(`Fatal error: ${data.type} - ${data.details}`);
          switch(data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              console.log('Network error, trying to recover...');
              hls.startLoad();
              break;
            case Hls.ErrorTypes.MEDIA_ERROR:
              console.log('Media error, trying to recover...');
              hls.recoverMediaError();
              break;
            default:
              console.log('Unrecoverable error');
              hls.destroy();
              break;
          }
        }
      });

      hls.loadSource(hlsUrl);
      hls.attachMedia(videoRef.current);

      return () => {
        hls.destroy();
      };
    } else if (videoRef.current?.canPlayType('application/vnd.apple.mpegurl')) {
      // Native HLS support (Safari)
      console.log('Using native HLS support');
      videoRef.current.src = hlsUrl;
      videoRef.current.addEventListener('loadedmetadata', () => {
        setLoading(false);
        videoRef.current?.play().catch(e => console.error('Error playing video:', e));
      });
      videoRef.current.addEventListener('error', (e) => {
        setError('Error loading video');
        console.error('Error loading video:', videoRef.current?.error);
      });
    } else {
      setError('HLS is not supported in this browser');
    }
  }, []);

  const handleVideoClick = () => {
    if (videoRef.current && videoRef.current.paused) {
      videoRef.current.play().catch(e => console.error('Error playing video on click:', e));
    }
  };

  return (
    <Card className="w-full relative">
      <CardContent className="p-4">
        <div className="relative">
          <video
            ref={videoRef}
            controls
            autoPlay
            muted
            playsInline
            onClick={handleVideoClick}
            className="w-full aspect-video bg-black rounded-lg"
          />
          {loading && !error && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/50 text-white">
              <p>Loading stream...</p>
            </div>
          )}
          {error && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/70 text-white">
              <p>{error}</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
