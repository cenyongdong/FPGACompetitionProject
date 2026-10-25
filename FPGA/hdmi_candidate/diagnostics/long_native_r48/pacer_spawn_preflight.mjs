// Local CPU-only gate. No sockets, board, SDK, datasets or model access.
import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import os from 'node:os';

const python = process.argv[2];
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const pacer = path.join(root, 'demo_v1/host/pacer.py');
const started = process.hrtime.bigint();
const base = { scope: 'local CPU only; no board/network/SDK', node: process.execPath,
    node_version: process.version, python, pacer, ticks: 6, hz: 30,
    automatic_retry: false };

function emit(result) {
    console.log(JSON.stringify({ ...base, ...result,
        elapsed_ms: Number(process.hrtime.bigint() - started) / 1e6 }));
    process.exitCode = result.passed ? 0 : 2;
}

if (!python || process.argv.length !== 3 || !path.isAbsolute(python)) {
    emit({ passed: false, error: 'Usage: node pacer_spawn_preflight.mjs ABSOLUTE_PYTHON_EXE',
        child_created: false, no_residual_child: true });
} else {
    // Match run.mjs's process-local priority requests; neither is a hard gate.
    try { os.setPriority(0, os.constants.priority.PRIORITY_ABOVE_NORMAL); } catch {}
    let child;
    try {
        child = spawn(python, [pacer, '6', '30'],
            { windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
    } catch (error) {
        emit({ passed: false, error: error.message, code: error.code,
            errno: error.errno, syscall: error.syscall, synchronous: true,
            child_created: false, no_residual_child: true });
    }
    if (child) {
        try { os.setPriority(child.pid, os.constants.priority.PRIORITY_ABOVE_NORMAL); } catch {}
        let stdout = '', stderr = '', spawnError = null, timedOut = false;
        child.stdout.on('data', data => { stdout += data; });
        child.stderr.on('data', data => { stderr += data; });
        child.on('error', error => {
            spawnError = { message: error.message, code: error.code,
                errno: error.errno, syscall: error.syscall };
        });
        // Only this newly-created six-tick CPU child may be terminated here.
        const timeout = setTimeout(() => { timedOut = true; child.kill(); }, 5000);
        child.on('close', (exitCode, signal) => {
            clearTimeout(timeout);
            const lines = stdout.trim() ? stdout.trim().split(/\r?\n/) : [];
            const sequenceOK = lines.length === 6 && lines.every((line, i) => line === String(i));
            emit({ passed: !spawnError && !timedOut && exitCode === 0 && signal === null &&
                    stderr.length === 0 && sequenceOK,
                pid: child.pid ?? null, child_created: child.pid !== undefined,
                child_closed: true, no_residual_child: true,
                exit_code: exitCode, signal, timed_out: timedOut,
                sequence_ok: sequenceOK, stdout: stdout.trim(), stderr: stderr.trim(),
                spawn_error: spawnError });
        });
    }
}
