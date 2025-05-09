import React, { forwardRef, useEffect, useImperativeHandle, useRef, useState } from 'react';
import { Card } from './card';
import { cn } from '@/lib/utils';
import { AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';

interface VideoTileProps extends React.HTMLAttributes<HTMLDivElement> {
  status?: 'online' | 'offline' | 'error';
  fallbackImage?: string;
  showControls?: boolean;
  aspectRatio?: 'square' | 'video' | 'vertical';
}

export const VideoTile = forwardRef<HTMLVideoElement, VideoTileProps>(({
  className,
  status = 'offline',
  fallbackImage,
  showControls = false,
  aspectRatio = 'video',
  ...props
}, ref) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [isStalled, setIsStalled] = useState(false);
  const stallTimeout = useRef<NodeJS.Timeout>();

  // Forward the video ref
  useImperativeHandle(ref, () => videoRef.current!, []);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleLoading = () => setIsLoading(true);
    const handleLoaded = () => {
      setIsLoading(false);
      setHasError(false);
      setIsStalled(false);
    };
    const handleError = () => {
      setHasError(true);
      setIsLoading(false);
    };
    const handleStalled = () => {
      // Only mark as stalled if it remains stalled for more than 3 seconds
      stallTimeout.current = setTimeout(() => {
        setIsStalled(true);
      }, 3000);
    };
    const handleUnstalled = () => {
      if (stallTimeout.current) {
        clearTimeout(stallTimeout.current);
      }
      setIsStalled(false);
    };
    const handleEnded = () => {
      // For HLS streams, ended usually means an error occurred
      setHasError(true);
      setIsLoading(false);
    };

    // Monitor video quality
    const checkVideoQuality = () => {
      if (video.readyState < 3) { // HAVE_FUTURE_DATA
        setIsStalled(true);
      } else {
        setIsStalled(false);
      }
    };
    const qualityInterval = setInterval(checkVideoQuality, 1000);

    video.addEventListener('loadstart', handleLoading);
    video.addEventListener('waiting', handleLoading);
    video.addEventListener('canplay', handleLoaded);
    video.addEventListener('error', handleError);
    video.addEventListener('stalled', handleStalled);
    video.addEventListener('playing', handleUnstalled);
    video.addEventListener('ended', handleEnded);

    return () => {
      video.removeEventListener('loadstart', handleLoading);
      video.removeEventListener('waiting', handleLoading);
      video.removeEventListener('canplay', handleLoaded);
      video.removeEventListener('error', handleError);
      video.removeEventListener('stalled', handleStalled);
      video.removeEventListener('playing', handleUnstalled);
      video.removeEventListener('ended', handleEnded);
      if (stallTimeout.current) {
        clearTimeout(stallTimeout.current);
      }
      clearInterval(qualityInterval);
    };
  }, []);

  return (
    <Card 
      className={cn(
        'relative overflow-hidden bg-black/90',
        {
          'aspect-square': aspectRatio === 'square',
          'aspect-video': aspectRatio === 'video',
          'aspect-[9/16]': aspectRatio === 'vertical',
        },
        className
      )}
      {...props}
    >
      <video
        ref={videoRef}
        className="h-full w-full object-contain"
        controls={showControls}
        playsInline
        autoPlay
        muted
      />

      {/* Status Overlay */}
      <div 
        className={cn(
          'absolute inset-0 flex items-center justify-center bg-black/50 transition-opacity duration-200',
          ((status === 'online' && !isLoading && !hasError && !isStalled) || showControls) ? 'opacity-0' : 'opacity-100'
        )}
      >
        {isLoading ? (
          <Loader2 className="h-8 w-8 animate-spin text-white" />
        ) : hasError || status === 'error' ? (
          <div className="text-center">
            <AlertCircle className="mx-auto h-8 w-8 text-red-500" />
            <p className="mt-2 text-sm text-white">Stream error</p>
          </div>
        ) : status === 'offline' ? (
          <div className="text-center">
            <AlertCircle className="mx-auto h-8 w-8 text-yellow-500" />
            <p className="mt-2 text-sm text-white">Stream offline</p>
          </div>
        ) : isStalled ? (
          <Loader2 className="h-8 w-8 animate-spin text-white opacity-50" />
        ) : null}
      </div>

      {/* Status Indicator */}
      <div className="absolute right-2 top-2 flex items-center gap-1.5 rounded-full bg-black/60 px-2 py-1">
        <div
          className={cn('h-2 w-2 rounded-full', {
            'bg-green-500': status === 'online' && !hasError && !isStalled,
            'bg-red-500': status === 'error' || hasError,
            'bg-yellow-500': status === 'offline' || isStalled,
          })}
        />
        <span className="text-xs text-white">
          {status === 'online' && !hasError && !isStalled ? 'Live' : 
           status === 'error' || hasError ? 'Error' :
           status === 'offline' ? 'Offline' : 
           isStalled ? 'Buffering' : 'Connecting...'}
        </span>
      </div>

      {/* Fallback Image */}
      {(hasError || status === 'offline') && fallbackImage && (
        <img
          src={fallbackImage}
          alt="Stream fallback"
          className="absolute inset-0 h-full w-full object-cover opacity-30"
        />
      )}
    </Card>
  );
});