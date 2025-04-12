import ffmpeg from 'ffmpeg-static';
import { spawn } from 'child_process';
import { storage } from './storage';

const RTSP_URL = 'rtsp://admin:1541Playdc7thst@10.1.10.239:8554/Streaming/Channels/201';
const HLS_OUTPUT_DIR = './public/hls';
const SEGMENT_DURATION = 2;

export class VideoProcessor {
  private ffmpegProcess: ReturnType<typeof spawn> | null = null;

  startStreaming() {
    const args = [
      '-i', RTSP_URL,
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

    this.ffmpegProcess = spawn(ffmpeg, args);

    this.ffmpegProcess.stderr?.on('data', (data) => {
      console.log('FFmpeg:', data.toString());
    });

    this.ffmpegProcess.on('error', (error) => {
      console.error('FFmpeg error:', error);
      storage.createEvent({
        type: 'ERROR',
        description: `FFmpeg error: ${error.message}`,
        objects: []
      });
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
