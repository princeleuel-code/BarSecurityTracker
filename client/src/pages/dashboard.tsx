import { useEffect, useRef } from "react";
import { Metric } from "@/components/ui/Metric";
import { VideoTile } from "@/components/ui/VideoTile";
import { TinyArea } from "@/components/charts/TinyArea";
import { useFeedHealth } from "@/hooks/useFeedHealth";
import { Activity, Timer } from "lucide-react";

export default function Dashboard() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const { status, bitrate, fps, history } = useFeedHealth("cam1");

  console.log('Dashboard rendering with status:', status);

  useEffect(() => {
    // Use a test pattern video instead of HLS
    if (videoRef.current) {
      videoRef.current.src = "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4";
      videoRef.current.play().catch(err => {
        console.error("Error playing video:", err);
      });
    }

    return () => {
      if (videoRef.current) {
        videoRef.current.pause();
        videoRef.current.src = "";
      }
    };
  }, []);

  // Calculate trend by comparing current value with average of previous minute
  const calculateTrend = (data: number[]) => {
    if (data.length < 2) return 0;
    const current = data[data.length - 1];
    const average = data.slice(0, -1).reduce((a, b) => a + b, 0) / (data.length - 1);
    return ((current - average) / average) * 100;
  };

  const bitrateHistory = history.map(h => h.bitrate);
  const fpsHistory = history.map(h => h.fps);

  return (
    <div className="grid grid-cols-12 gap-4 p-6 bg-slate-950 text-slate-100 min-h-screen">
      {/* Left column – live feed */}
      <div className="col-span-8">
        <VideoTile
          ref={videoRef}
          status={status}
          aspectRatio="video"
          className="w-full"
        />
      </div>

      {/* Right column – metrics */}
      <div className="col-span-4 space-y-4">
        <Metric
          label="Feed status"
          value={status.toUpperCase()}
        />

        <Metric
          label="Bit-rate"
          value={Math.round(bitrate)}
          unit="kbps"
          trend={calculateTrend(bitrateHistory)}
        />

        <div className="bg-card p-4 rounded-lg border">
          <div className="flex items-center gap-2 mb-2">
            <Activity className="w-4 h-4 text-muted-foreground" />
            <h3 className="text-sm font-medium">Bit-rate (kbps)</h3>
          </div>
          <TinyArea
            data={bitrateHistory}
            color="#22c55e"
          />
        </div>

        <Metric
          label="Frame rate"
          value={Math.round(fps)}
          unit="fps"
          trend={calculateTrend(fpsHistory)}
        />

        <div className="bg-card p-4 rounded-lg border">
          <div className="flex items-center gap-2 mb-2">
            <Timer className="w-4 h-4 text-muted-foreground" />
            <h3 className="text-sm font-medium">Frame rate (fps)</h3>
          </div>
          <TinyArea
            data={fpsHistory}
            color="#0ea5e9"
          />
        </div>
      </div>
    </div>
  );
}
