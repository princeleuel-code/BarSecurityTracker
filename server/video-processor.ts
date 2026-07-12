import ffmpeg from 'ffmpeg-static';
import { spawn } from 'child_process';
import { storage } from './storage';

const HLS_OUTPUT_DIR = './public/hls';
const SEGMENT_DURATION = 2;
const ALLOWED_STREAM_PROTOCOLS = new Set(['rtsp:', 'rtsps:']);

function getCameraStreamUrl(): string {
  const configuredUrl = process.env.CAMERA_RTSP_URL ?? process.env.RTSP_URL;

  if (!configuredUrl) {
    throw new Error('CAMERA_RTSP_URL or RTSP_URL is required');
  }

  let parsedUrl: URL;
  try {
    parsedUrl = new URL(configuredUrl);
  } catch {
    throw new Error('The configured camera stream URL is invalid');
  }

  if (!ALLOWED_STREAM_PROTOCOLS.has(parsedUrl.protocol)) {
    throw new Error('The camera stream URL must use rtsp:// or rtsps://');
  }

  return configuredUrl;
}

function redactCredentials(value: string): string {
  return value.replace(/(rtsps?:\/\/)([^\s/@:]+):([^\s/@]+)@/gi, '$1***:***@');
}

export class VideoProcessor {
  private ffmpegProcess: ReturnType<typeof spawn> | null = null;

  startStreaming() {
    if (this.ffmpegProcess) {
      return;
    }

    let streamUrl: string;
    try {
      streamUrl = getCameraStreamUrl();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Camera configuration failed';
      storage.createEvent({
        type: 'ERROR',
        description: message,
        objects: []
      });
      throw error;
    }

    if (!ffmpeg) {
      throw new Error('FFmpeg executable is unavailable');
    }

    const args = [
      '-hide_banner',
      '-loglevel', 'warning',
      '-i', streamUrl,
      '-c:v', 'libx264',
      '-preset', 'veryfast',
      '-tune', 'zerolatency',
      '-c:a', 'aac',
      '-f', 'hls',
      '-hls_time', SEGMENT_DURATION.toString(),
      '-hls_list_size', '3',
      '-hls_flags', 'delete_segments',
      '-hls_segment_filename', `${HLS_OUTPUT_DIR}/segment_%d.ts`,
      `${HLS_OUTPUT_DIR}/playlist.m3u8`
    ];

    this.ffmpegProcess = spawn(ffmpeg, args, {
      stdio: ['ignore', 'ignore', 'pipe']
    });

    this.ffmpegProcess.stderr?.on('data', (data) => {
      console.error('FFmpeg:', redactCredentials(data.toString()));
    });

    this.ffmpegProcess.on('error', (error) => {
      const safeMessage = redactCredentials(error.message);
      console.error('FFmpeg error:', safeMessage);
      storage.createEvent({
        type: 'ERROR',
        description: `FFmpeg error: ${safeMessage}`,
        objects: []
      });
    });

    this.ffmpegProcess.on('exit', () => {
      this.ffmpegProcess = null;
    });
  }

  stopStreaming() {
    if (this.ffmpegProcess) {
      this.ffmpegProcess.kill();
      this.ffmpegProcess = null;
    }
  }
}

export const videoProcessor = new VideoProcessor();
