import ffmpeg from 'ffmpeg-static';
import { spawn } from 'child_process';
import { storage } from './storage';

const HLS_OUTPUT_DIR = './public/hls';
const SEGMENT_DURATION = 2;
const ALLOWED_STREAM_PROTOCOLS = new Set(['rtsp:', 'rtsps:']);

/**
 * Reads and validates the camera stream URL without providing an unsafe default.
 * Production must fail closed when the configured camera is unavailable.
 */
export