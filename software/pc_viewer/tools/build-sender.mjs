import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { ROOT, WORK, EXE } from '../paths.mjs';
fs.mkdirSync(WORK, { recursive: true });
const src = path.join(ROOT, 'software/pose_output');
const args = ['-std=c++17', '-O2', '-Wall', '-Wextra', '-Wpedantic', '-ffp-contract=off',
    ...['pose_frame.cpp','tcp_sender.cpp','replay.cpp'].map(f => path.join(src, f)), '-o', EXE];
if (process.platform === 'win32') args.push('-static', '-lws2_32');
const result = spawnSync(process.env.CXX || 'g++', args, { encoding: 'utf8', windowsHide: true });
fs.writeFileSync(path.join(WORK, 'build.txt'), [args.join('\n'), result.stdout, result.stderr].join('\n'));
if (result.error || result.status !== 0) throw result.error || new Error(result.stderr);
console.log(JSON.stringify({ built: EXE, exit: result.status }));
