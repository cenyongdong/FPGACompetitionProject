import { fileURLToPath } from 'node:url';
import path from 'node:path';
export const HERE = path.dirname(fileURLToPath(import.meta.url));
export const ROOT = path.resolve(HERE, '../..');
export const WORK = path.join(ROOT, '.local/pc-pose-replay-20261018-r1');
export const EXE = path.join(WORK, process.platform === 'win32' ? 'pose_replay.exe' : 'pose_replay');
