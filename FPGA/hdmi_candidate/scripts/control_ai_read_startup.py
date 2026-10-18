"""Prepare and supervise the one approved read-v3 startup. Default: offline.

This module never creates an approval. Capture/reboot modes require the actual
new human receipt, the current complete manifest review, and an unpaused task.
The remote source uses the same independent guards as the finite DMA adapter.
"""
from pathlib import Path
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / '.local/hdmi-live-20261017-r3'
EVIDENCE = ROOT / 'tools/pose-v1/evidence/hdmi-live-20261017-r3'
POWERSHELL = Path('C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe')
KINDS = {'candidate': ('uart_candidate', 'candidate_reboot'),
         'fallback': ('uart_fallback', 'original_fallback_reboot')}


def need(okay, message):
    if not okay:
        raise RuntimeError(message)


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def import_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def configuration():
    generator = import_file('read_remote_generator_for_startup', WORK / 'prepare_remote_read_v3.py')
    cfg, review = generator.actual_configuration()
    return generator, cfg, review


def approval(action, approved, receipt):
    generator, cfg, review = configuration()
    planner = generator.load_planner()
    context, checked = planner.review_manifest()
    need(checked == review, 'Local manifest review changed within startup gate')
    planner.require_approval(action, context, approved, receipt)
    return generator, cfg, review


def process_identity(pid, require_running=True):
    """Read PID, creation time and image without opening a serial device."""
    need(os.name == 'nt', 'Actual capture supervision requires Windows')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x1000, False, int(pid))
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        created, exited, cpu_kernel, cpu_user = (wintypes.FILETIME() for _ in range(4))
        need(kernel.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(exited),
                                    ctypes.byref(cpu_kernel), ctypes.byref(cpu_user)), 'Cannot read UART process creation time')
        image = ctypes.create_unicode_buffer(32768)
        count = wintypes.DWORD(len(image))
        need(kernel.QueryFullProcessImageNameW(handle, 0, image, ctypes.byref(count)), 'Cannot verify UART process image')
        status = wintypes.DWORD()
        need(kernel.GetExitCodeProcess(handle, ctypes.byref(status)), 'Cannot read UART process status')
        if require_running:
            need(status.value == 259, 'UART process already exited')
        result = {'pid': int(pid), 'creation_filetime': (created.dwHighDateTime << 32) | created.dwLowDateTime,
                  'image': str(Path(image.value).resolve()).lower()}
        if not require_running:
            result['exit_code'] = status.value
        return result
    finally:
        kernel.CloseHandle(handle)


CAPTURE = r'''$ErrorActionPreference = 'Stop'
$taskOut = @@OUT@@
$taskManifest = @@MANIFEST@@
$taskReceipt = @@RECEIPT@@
$taskState = @@STATE@@
$taskManifestSHA = @@MANIFEST_SHA@@
$taskReviewSHA = @@REVIEW_SHA@@
$taskReceiptSHA = @@RECEIPT_SHA@@
$taskAction = @@ACTION@@
$taskUSB = @@USB@@
$taskPortName = @@PORT@@
$taskResult = [ordered]@{port=$taskPortName;usb_identity=$taskUSB;baud=115200;framing='8N1';dtr=$false;rts=$false;transmitted_bytes=0;opened=$false;pid=$PID;byte_budget=4194304;seconds_budget=300;received_bytes=0;started=(Get-Date).ToString('o')}
$taskPort = $null
$taskStream = $null
try {
    if ((Get-FileHash -LiteralPath $taskManifest -Algorithm SHA256).Hash.ToLower() -ne $taskManifestSHA) {throw 'Manifest changed before UART open'}
    if ((Get-FileHash -LiteralPath $taskReceipt -Algorithm SHA256).Hash.ToLower() -ne $taskReceiptSHA) {throw 'Bound approval changed before UART open'}
    $taskAuth = Get-Content -Raw -LiteralPath $taskReceipt | ConvertFrom-Json
    $taskLive = Get-Content -Raw -LiteralPath $taskState | ConvertFrom-Json
    if (-not $taskAuth.approved -or -not $taskAuth.active -or $taskAuth.approved_by -ne 'user' -or $taskAuth.package_id -ne 'ai-read-v3' -or $taskAuth.manifest_sha256 -ne $taskManifestSHA -or $taskAuth.local_review_sha256 -ne $taskReviewSHA -or -not ($taskAuth.allowed_actions -contains $taskAction) -or $taskAuth.old_DATA -ne 'paused' -or $taskAuth.filesystem_repair -ne $false -or [string]::IsNullOrWhiteSpace($taskAuth.user_confirmation)) {throw 'New bound UART approval absent'}
    if ($taskLive.status -like 'paused*') {throw 'Task paused before UART open'}
    $taskInventory = @(Get-CimInstance Win32_SerialPort | Where-Object {$_.DeviceID -eq $taskPortName})
    if ($taskInventory.Count -ne 1 -or $taskInventory[0].PNPDeviceID -cne $taskUSB -or $taskInventory[0].Status -ne 'OK') {throw 'Actual UART USB identity changed'}
    $taskPort = New-Object System.IO.Ports.SerialPort($taskPortName,115200,[System.IO.Ports.Parity]::None,8,[System.IO.Ports.StopBits]::One)
    $taskPort.DtrEnable = $false
    $taskPort.RtsEnable = $false
    $taskPort.Handshake = [System.IO.Ports.Handshake]::None
    $taskPort.ReadTimeout = 250
    $taskPort.WriteTimeout = 250
    $taskStream = [IO.File]::Open((Join-Path $taskOut 'rx.bin'),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
    $taskPort.Open()
    $taskResult.opened = $true
    $taskResult | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskOut 'ready.tmp') -Encoding UTF8
    Move-Item -LiteralPath (Join-Path $taskOut 'ready.tmp') -Destination (Join-Path $taskOut 'ready.json') -ErrorAction Stop
    $taskWatch = [Diagnostics.Stopwatch]::StartNew()
    while ($taskWatch.Elapsed.TotalSeconds -lt 300 -and $taskResult.received_bytes -lt 4194304 -and -not (Test-Path -LiteralPath (Join-Path $taskOut 'stop'))) {
        $taskCount = [Math]::Min($taskPort.BytesToRead,4194304-$taskResult.received_bytes)
        if ($taskCount -gt 0) {
            $taskBuffer = New-Object byte[] $taskCount
            $taskRead = $taskPort.Read($taskBuffer,0,$taskCount)
            $taskStream.Write($taskBuffer,0,$taskRead)
            $taskStream.Flush()
            $taskResult.received_bytes += $taskRead
        }
        Start-Sleep -Milliseconds 50
    }
    $taskResult.capture_seconds = $taskWatch.Elapsed.TotalSeconds
    $taskResult.stopped_on_request = Test-Path -LiteralPath (Join-Path $taskOut 'stop')
} catch {
    $taskResult.error = $_.Exception.Message
} finally {
    if ($null -ne $taskPort) {if ($taskPort.IsOpen) {$taskPort.Close()};$taskPort.Dispose()}
    if ($null -ne $taskStream) {$taskStream.Dispose()}
    $taskResult.closed = $true
    $taskResult.finished = (Get-Date).ToString('o')
    $taskResult | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $taskOut 'reader.json') -Encoding UTF8
}
$taskResult | ConvertTo-Json
if ($taskResult.Contains('error')) {exit 1}
'''


def ps_literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def capture_source(cfg, kind, receipt):
    need(kind in KINDS, 'Unknown startup kind')
    values = {'OUT': capture_dir(kind), 'MANIFEST': EVIDENCE / 'controlled-startup-read-v3/manifest.json',
              'RECEIPT': Path(receipt).resolve(), 'STATE': EVIDENCE / 'continuation-state.json',
              'MANIFEST_SHA': cfg['manifest_sha256'], 'REVIEW_SHA': cfg['local_review_sha256'],
              'RECEIPT_SHA': sha(receipt),
              'ACTION': KINDS[kind][0], 'USB': cfg['board']['uart_usb_identity'],
              'PORT': cfg['board']['uart_port']}
    source = CAPTURE
    for key, value in values.items():
        source = source.replace('@@' + key + '@@', ps_literal(value))
    need('@@' not in source, 'Unresolved UART source token')
    return source


def capture_dir(kind):
    return EVIDENCE / ('uart-' + kind + '-read-v3')


def require_live_uart(cfg, kind, receipt):
    directory = capture_dir(kind)
    ready, owned = load(directory / 'ready.json'), load(directory / 'owned-process.json')
    need(ready.get('opened') is True and ready.get('transmitted_bytes') == 0 and
         ready.get('port') == cfg['board']['uart_port'] and
         ready.get('usb_identity') == cfg['board']['uart_usb_identity'] and
         ready.get('pid') == owned.get('pid'), 'UART ready does not identify this capture')
    need(not (directory / 'reader.json').exists() and not (directory / 'stop').exists(), 'UART capture already ended')
    need(process_identity(owned['pid']) == owned['process_identity'], 'UART PID reused or changed')
    need((directory / 'capture.ps1').read_text(encoding='utf-8') == capture_source(cfg, kind, receipt),
         'Current capture source differs from reviewed actual configuration')
    return ready


def close_capture(kind, seconds=5):
    """Request and verify only this bounded receive-only reader's cleanup."""
    directory = capture_dir(kind)
    owned = load(directory / 'owned-process.json')
    save(directory / 'stop', {'reason': 'Fresh SSH boot observed; close owned UART'})
    deadline = time.monotonic() + seconds
    report = {'pid': owned['pid'], 'closed': False, 'owned_process_exited': False,
              'seconds_budget': seconds, 'kill_or_terminate_used': False}
    while time.monotonic() < deadline:
        try:
            reader = load(directory / 'reader.json') if (directory / 'reader.json').exists() else {}
            report['closed'] = reader.get('closed') is True and reader.get('pid') == owned['pid']
            seen = process_identity(owned['pid'], require_running=False)
            identity = {key: seen[key] for key in ('pid', 'creation_filetime', 'image')}
            report['owned_process_exited'] = identity != owned['process_identity'] or seen['exit_code'] != 259
        except OSError as error:
            # ERROR_INVALID_PARAMETER means this PID no longer exists. Access
            # denial or another query failure cannot prove process cleanup.
            report['owned_process_exited'] = getattr(error, 'winerror', None) == 87
            report['process_query_error'] = str(error)
        except Exception as error:
            report['observation_error'] = str(error)
        if report['closed'] and report['owned_process_exited']:
            break
        time.sleep(min(.1, max(0, deadline - time.monotonic())))
    save(directory / 'close-observation.json', report)
    return report


def capture(kind, approved, receipt):
    _, cfg, _ = approval(KINDS[kind][0], approved, receipt)
    out = capture_dir(kind)
    out.mkdir(exist_ok=False)
    source = capture_source(cfg, kind, receipt)
    (out / 'capture.ps1').write_text(source, encoding='utf-8')
    save(out / 'local-entry.json', {'manifest_sha256': cfg['manifest_sha256'],
         'local_review_sha256': cfg['local_review_sha256'], 'action': KINDS[kind][0],
         'source_sha256': sha(out / 'capture.ps1'), 'new_approval_checked': True})
    # Recheck immediately before the only process launch; the child rechecks
    # approval, manifest, pause and USB identity immediately before opening.
    approval(KINDS[kind][0], approved, receipt)
    process = None
    try:
        with (out / 'stdout.txt').open('xb') as stdout, (out / 'stderr.txt').open('xb') as stderr:
            process = subprocess.Popen([str(POWERSHELL), '-NoProfile', '-NonInteractive', '-ExecutionPolicy',
                                        'Bypass', '-File', str(out / 'capture.ps1')], stdout=stdout, stderr=stderr,
                                       creationflags=subprocess.CREATE_NO_WINDOW)
            # This minimal PID record precedes every fallible identity query.
            save(out / 'owned-pid.json', {'pid': process.pid, 'source_sha256': sha(out / 'capture.ps1')})
            save(out / 'owned-process.json', {'pid': process.pid, 'process_identity': process_identity(process.pid),
                 'source_sha256': sha(out / 'capture.ps1'), 'seconds_budget': 300, 'byte_budget': 4194304})
        started = time.monotonic()
        while time.monotonic() - started < 10 and process.poll() is None:
            if (out / 'ready.json').exists():
                ready = require_live_uart(cfg, kind, receipt)
                print(json.dumps({'capture_started': True, 'ready': ready, 'directory': str(out)}))
                return
            time.sleep(.1)
        raise RuntimeError('UART not verified ready; no reboot permitted')
    except BaseException as original:
        # Preserve the original cause even if logging or close supervision also
        # fails. Only this receive-only reader is asked to stop. It also has an
        # independent 300s limit; no unrelated port/process is touched.
        extra = []
        if process is not None:
            print('OWNED_UART_PID ' + str(process.pid), file=sys.stderr, flush=True)
            try:
                save(out / 'stop', {'reason': 'capture launch/ready failure', 'error': str(original)})
            except BaseException as error:
                extra.append('stop: ' + str(error))
            try:
                process.wait(timeout=3)
            except BaseException as error:
                extra.append('wait: ' + str(error))
        failure = {'error': str(original), 'pid': process.pid if process else None,
                   'exit': process.poll() if process else None,
                   'still_running': process is not None and process.poll() is None,
                   'secondary_errors': extra, 'no_reboot_permitted': True}
        try:
            save(out / 'startup-failure.json', failure)
        except BaseException as error:
            failure['evidence_error'] = str(error)
        print(json.dumps(failure), file=sys.stderr, flush=True)
        raise


def reboot_source(generator, cfg, kind):
    action = KINDS[kind][1]
    source = generator.render_guard_prefix(cfg, action, kind + '-reboot')
    if kind == 'candidate':
        body = """
runtime_guard(True)
identity = CFG['board']['pre_start_boot_id']
installed = record('install.json')
need(installed.get('passed') is True and installed.get('boot_id') == identity and
     installed.get('BOOT_sha256') == CFG['files']['BOOT-ai-read-v3.bin']['sha256'] and
     installed.get('full_readback_bytes') == 7023552 and installed.get('other_startup_files_unchanged') is True and
     installed.get('boot_partition_unmounted') is True, 'Candidate full install proof absent')
audit(CFG['files']['BOOT-ai-read-v3.bin']['sha256'], identity)
checked_backup()
need(not (META/'candidate-startup.json').exists(), 'Candidate already started')
request = 'candidate-reboot-request.json'
"""
    else:
        body = """
runtime_guard(True)
identity = restored_identity()
preflight = record('fallback-preflight.json')
need(preflight.get('passed') is True and preflight.get('read_only') is True and
     preflight.get('boot_id') == identity and preflight.get('one_original_fallback_preconditions') is True and
     preflight.get('BOOT_write') is False, 'Current read-only fallback preflight absent')
audit(CFG['original_boot_sha256'], identity)
checked_backup()
failure = record('failure-evidence-review.json')
need(failure.get('preserved') is True and failure.get('boot_id') == identity and bool(failure.get('files')),
     'Failure evidence preservation receipt absent')
for name, row in failure['files'].items():
    relative = PurePosixPath(name)
    need(not relative.is_absolute() and '..' not in relative.parts, 'Unsafe failure evidence path')
    verify_file(ROOT.joinpath(*relative.parts), row)
request = 'original-fallback-reboot-request.json'
"""
    return source + body + """
reserve(STAGE)
save_new(META/request, identity_record({'old_boot_id': identity, 'one_command_attempt_reserved': True,
         'BOOT_write': False, 'time_unix': time.time(), 'pid': os.getpid()}))
print('AI_READ_REBOOT_PREFLIGHT ' + json.dumps(identity_record({'passed': True, 'old_boot_id': identity,
      'one_command_attempt_reserved': True, 'BOOT_write': False})), flush=True)
subprocess.run(['/sbin/reboot'], check=True, timeout=10)
"""


def marked_json(stdout, marker):
    rows = [line[len(marker):] for line in stdout.decode('utf-8', errors='replace').splitlines()
            if line.startswith(marker)]
    need(len(rows) == 1, 'Exactly one tagged transport result required')
    return json.loads(rows[0])


def transport(code, out, timeout):
    # A complete guard prefix exceeds Windows' command-line bound. Reuse the
    # reviewed executor's small-argv OpenSSH and exact regular-file stdin;
    # its separate askpass supplies authentication only in memory. The caller
    # has already checked this exact adapter's SHA in the approved manifest.
    executor = import_file('read_v3_startup_transport', WORK / 'execute_read_v3.py')
    return executor.transport_bounded(code, out, timeout, timeout + 10)


def reboot(kind, approved, receipt):
    generator, cfg, review = approval(KINDS[kind][1], approved, receipt)
    require_live_uart(cfg, kind, receipt)
    out = EVIDENCE / (kind + '-startup-read-v3')
    out.mkdir(exist_ok=False)
    code = reboot_source(generator, cfg, kind)
    compile(code, str(out / 'remote-code.py'), 'exec')
    (out / 'remote-code.py').write_text(code, encoding='utf-8')
    save(out / 'reservation.json', {'action': KINDS[kind][1], 'one_command_attempt_reserved': True,
         'manifest_sha256': cfg['manifest_sha256'], 'local_review_sha256': review['local_review_sha256'],
         'new_approval_checked': True, 'no_automatic_retry': True, 'BOOT_write': False})
    approval(KINDS[kind][1], approved, receipt)
    require_live_uart(cfg, kind, receipt)
    started = time.monotonic()
    stdout, status, _ = transport(code, out, 25)
    need(status is not None, 'Original owned transport is still running; monitor it before any reconnect')
    preflight = marked_json(stdout, 'AI_READ_REBOOT_PREFLIGHT ')
    need(preflight.get('passed') is True and preflight.get('manifest_sha256') == cfg['manifest_sha256'] and
         preflight.get('local_review_sha256') == cfg['local_review_sha256'] and
         preflight.get('one_command_attempt_reserved') is True, 'Reboot preflight proof absent; never resend')
    old = preflight['old_boot_id']
    if kind == 'candidate':
        need(old == cfg['board']['pre_start_boot_id'], 'Candidate preflight used another boot')
    observations, fresh, live_transport = [], None, None
    deadline = started + 180
    query = "import pathlib,json;print('AI_READ_BOOT_WATCH '+json.dumps({'boot_id':pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'uptime':pathlib.Path('/proc/uptime').read_text().strip()}))"
    while time.monotonic() < deadline:
        # A later pause revokes permission to continue; read-only observations
        # and evidence retention may be completed, but no extra reboot is sent.
        state = load(EVIDENCE / 'continuation-state.json')
        if str(state.get('status', '')).startswith('paused'):
            break
        remaining = deadline - time.monotonic()
        # The transport adds a ten-second outer allowance. Never start a
        # connection whose complete observation window exceeds the remainder.
        inner_budget = min(8, int(remaining) - 10)
        if inner_budget < 1:
            break
        item_out = out / ('watch-' + str(len(observations)))
        item_out.mkdir()
        data, status, expired = transport(query, item_out, inner_budget)
        item = {'index': len(observations), 'exit': status, 'timeout': expired,
                'seconds': time.monotonic() - started}
        if status == 0 and not expired:
            try:
                observed = marked_json(data, 'AI_READ_BOOT_WATCH ')
                need(isinstance(observed.get('boot_id'), str) and
                     re.fullmatch('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', observed['boot_id']),
                     'Invalid returned boot identity')
                item.update(observed)
                if observed['boot_id'] != old:
                    fresh = observed
            except Exception as error:
                item['parse_error'] = str(error)
        observations.append(item)
        save(item_out / 'observation.json', item)
        if status is None:
            live_transport = str(item_out / 'owned-process.json')
            break
        if fresh:
            break
        time.sleep(min(3, max(0, deadline - time.monotonic())))
    result = {'passed': fresh is not None, 'package_id': cfg['package_id'],
              'manifest_sha256': cfg['manifest_sha256'], 'local_review_sha256': cfg['local_review_sha256'],
              'old_boot_id': old, 'boot_id': fresh['boot_id'] if fresh else None,
              'seconds': time.monotonic() - started, 'BOOT_write': False, 'new_Device_Open': 0,
              'live_transport_requires_monitoring': live_transport,
              'candidate_reboot_commands' if kind == 'candidate' else 'original_fallback_reboot_commands': 1}
    save(out / 'result.json', result)
    if fresh:
        result['UART_cleanup'] = close_capture(kind)
        save(out / 'cleanup-result.json', result['UART_cleanup'])
    print(json.dumps(result))
    need(fresh is not None, 'No new boot observed; keep UART evidence and never issue a second reboot')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['inspect', 'capture', 'reboot'], nargs='?', default='inspect')
    parser.add_argument('--kind', choices=KINDS, default='candidate')
    parser.add_argument('--approved', action='store_true')
    parser.add_argument('--approval-file', type=Path)
    args = parser.parse_args()
    if args.mode == 'inspect':
        generator, cfg, review = configuration()
        code = reboot_source(generator, cfg, args.kind)
        compile(code, '<offline-read-v3-reboot>', 'exec')
        print(json.dumps({'offline_only': True, 'remote_reboot_source_sha256': hashlib.sha256(code.encode()).hexdigest(),
                          'local_review_sha256': review['local_review_sha256'], 'board_actions': 0}))
    elif args.mode == 'capture':
        capture(args.kind, args.approved, args.approval_file)
    else:
        reboot(args.kind, args.approved, args.approval_file)


if __name__ == '__main__':
    main()
