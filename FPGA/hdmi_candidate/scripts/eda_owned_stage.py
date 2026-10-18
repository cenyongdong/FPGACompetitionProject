"""One bounded EDA job; quiet phases need owned CPU progress, not log traffic.

The old log-only monitor and its stopped run remain unchanged. This supervisor
records only its own process tree, preserves the actual policy, and never starts
a duplicate job or changes EDA timing/DRC/strategy settings.
"""
from pathlib import Path
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
import subprocess
import time

R = Path(__file__).resolve().parents[3]
E = R / 'tools/pose-v1/evidence/hdmi-live-20261017-r3'
W = R / '.local/hdmi-live-20261017-r3'


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


class Memory(ctypes.Structure):
    _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong)] + [
        (name, ctypes.c_ulonglong) for name in
        ['totalPhys', 'availPhys', 'totalPage', 'availPage', 'totalVirt', 'availVirt', 'availExt']]


def memory():
    value = Memory()
    value.length = ctypes.sizeof(value)
    assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(value))
    return {'available_MB': value.availPhys // 1048576, 'load_percent': value.load,
            'available_commit_MB': value.availPage // 1048576}


class ProcessEntry(ctypes.Structure):
    _fields_ = [('dwSize', wintypes.DWORD), ('cntUsage', wintypes.DWORD),
                ('th32ProcessID', wintypes.DWORD), ('th32DefaultHeapID', ctypes.c_size_t),
                ('th32ModuleID', wintypes.DWORD), ('cntThreads', wintypes.DWORD),
                ('th32ParentProcessID', wintypes.DWORD), ('pcPriClassBase', wintypes.LONG),
                ('dwFlags', wintypes.DWORD), ('szExeFile', wintypes.WCHAR * 260)]


def owned_cpu(root):
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    snapshot = kernel.CreateToolhelp32Snapshot(2, 0)
    if snapshot == wintypes.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    table = {}
    try:
        entry = ProcessEntry()
        entry.dwSize = ctypes.sizeof(entry)
        okay = kernel.Process32FirstW(snapshot, ctypes.byref(entry))
        while okay:
            table[int(entry.th32ProcessID)] = (int(entry.th32ParentProcessID), entry.szExeFile)
            okay = kernel.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel.CloseHandle(snapshot)
    selected = {int(root)}
    while True:
        expanded = selected | {pid for pid, row in table.items() if row[0] in selected}
        if expanded == selected:
            break
        selected = expanded
    result = []
    for pid in sorted(selected):
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            continue
        try:
            created, exited, system, user = (wintypes.FILETIME() for _ in range(4))
            status = wintypes.DWORD()
            if not kernel.GetProcessTimes(handle, ctypes.byref(created), ctypes.byref(exited),
                                          ctypes.byref(system), ctypes.byref(user)):
                continue
            if not kernel.GetExitCodeProcess(handle, ctypes.byref(status)) or status.value != 259:
                continue
            as_int = lambda value: (value.dwHighDateTime << 32) | value.dwLowDateTime
            result.append({'pid': pid, 'parent': table.get(pid, (None, ''))[0],
                           'image': table.get(pid, (None, ''))[1],
                           'creation_filetime': as_int(created),
                           'CPU_seconds': (as_int(system) + as_int(user)) / 1e7})
        finally:
            kernel.CloseHandle(handle)
    return result


def choose_extension(budget, ceiling, size, prior_size, age, cpu_delta, error, resource):
    progress = (size > prior_size and age < 180) or cpu_delta >= 1.
    return (budget < ceiling and progress and not error and
            resource['available_MB'] > 350 and resource['available_commit_MB'] > 800)


def stage(name, tcl, ceiling=1800, run_names=None):
    out, work = E / name, W / name
    out.mkdir(exist_ok=False)
    work.mkdir(exist_ok=False)
    tcl = tcl.replace('@@OUT@@', out.as_posix()).replace('@@REF@@', (W / 'reference').as_posix()).replace('@@WORK@@', work.as_posix())
    (out / 'stage.tcl').write_text(tcl, encoding='utf-8')
    (work / 'stage.tcl').write_text(tcl, encoding='utf-8')
    (out / 'actual-supervisor.py').write_bytes(Path(__file__).read_bytes())
    env = os.environ.copy()
    env.update(PROCESSOR_ARCHITECTURE='AMD64', XILINX_VIVADO='D:/vivado18.3/Vivado/2018.3',
               JFM_PATH=str(W / 'reference'), FMSH_PROCISE_PATH='C:/FudanMicro/Procise')
    for key in list(env):
        if key.startswith('RDI_'):
            env.pop(key)
    command = ['D:/vivado18.3/Vivado/2018.3/bin/vivado.bat', '-mode', 'batch', '-nojournal',
               '-log', str(out / 'vivado.log'), '-source', str(work / 'stage.tcl')]
    started, budget, prior_size, cpu_total, cpu_at_decision = time.monotonic(), 180, 0, 0., 0.
    decisions, samples, prior_cpu, process, stopped = [], [], {}, None, False
    last_sample = -30.
    try:
        with (out / 'stdout.txt').open('xb') as stdout, (out / 'stderr.txt').open('xb') as stderr:
            process = subprocess.Popen(command, cwd=work, env=env, stdout=stdout, stderr=stderr,
                                       creationflags=subprocess.CREATE_NO_WINDOW)
            dump(out / 'owned-process.json', {'pid': process.pid, 'initial_budget': 180, 'ceiling': ceiling,
                 'work': str(work), 'resource_at_start': memory(), 'supervisor_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
            while process.poll() is None:
                elapsed = time.monotonic() - started
                if elapsed - last_sample >= 30:
                    rows = owned_cpu(process.pid)
                    for row in rows:
                        identity = (row['pid'], row['creation_filetime'])
                        cpu_total += max(0., row['CPU_seconds'] - prior_cpu.get(identity, 0.))
                        prior_cpu[identity] = row['CPU_seconds']
                    samples.append({'elapsed': elapsed, 'owned_processes': rows, 'accumulated_owned_CPU_seconds': cpu_total})
                    dump(out / 'owned-cpu-samples.json', samples)
                    last_sample = elapsed
                if elapsed >= budget:
                    run_root = W / 'reference/fpai_demo_vivado.runs'
                    roots = [run_root] if run_names is None else [run_root / name for name in run_names]
                    logs = [file for root in roots for file in root.rglob('*.log')] + [out / 'stdout.txt', out / 'vivado.log']
                    logs = [file for file in logs if file.exists()]
                    size = sum(file.stat().st_size for file in logs)
                    age = min((time.time() - file.stat().st_mtime for file in logs), default=1e9)
                    error = any('ERROR:' in file.read_text(encoding='utf-8', errors='replace')[-24000:] for file in logs)
                    resource = memory()
                    cpu_delta = cpu_total - cpu_at_decision
                    extend = choose_extension(budget, ceiling, size, prior_size, age, cpu_delta, error, resource)
                    item = {'elapsed': elapsed, 'previous_budget': budget,
                            'new_budget': min(budget + 180, ceiling) if extend else budget,
                            'log_bytes': size, 'youngest_log_age_seconds': age,
                            'owned_CPU_delta_seconds': cpu_delta, 'error_seen': error, 'memory': resource,
                            'action': 'continue original owned process' if extend else 'stop and preserve'}
                    decisions.append(item)
                    dump(out / 'timeout-decisions.json', decisions)
                    print(json.dumps(item), flush=True)
                    if extend:
                        budget, prior_size, cpu_at_decision = min(budget + 180, ceiling), size, cpu_total
                    else:
                        stopped = True
                        cleanup = subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True, timeout=20)
                        (out / 'cleanup.txt').write_bytes(cleanup.stdout + cleanup.stderr)
                        try:
                            process.wait(timeout=20)
                        except subprocess.TimeoutExpired:
                            pass
                        break
                time.sleep(1)
    except BaseException as error:
        dump(out / 'controller-error.json', {'error': str(error), 'pid': process.pid if process else None,
             'exit': process.poll() if process else None, 'source_or_constraint_changes': False})
        if process is not None and process.poll() is None:
            cleanup = subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True, timeout=20)
            (out / 'cleanup-after-error.txt').write_bytes(cleanup.stdout + cleanup.stderr)
        raise
    result = {'exit': process.poll(), 'seconds': time.monotonic() - started, 'initial_budget_seconds': 180,
              'final_budget_seconds': budget, 'ceiling_seconds': ceiling, 'stopped_by_monitor': stopped,
              'decisions': decisions, 'final_memory': memory(), 'owned_CPU_seconds': cpu_total,
              'quiet_phase_CPU_evidence_allowed': True}
    dump(out / 'execution.json', result)
    print(json.dumps(result), flush=True)
    if process.poll() != 0 or stopped:
        raise RuntimeError('EDA failed/stopped; preserve and diagnose before dependent steps')
    return out
