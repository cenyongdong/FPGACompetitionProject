"""Bounded UDP stimulus with a monotonic send ledger; send != radio frame."""
import argparse
import csv
from contextlib import contextmanager
import ipaddress
import json
import os
from pathlib import Path
import socket
import struct
import time


@contextmanager
def timing_scope(enabled):
    """Temporary process-local Windows timing; always restore on exit."""
    status = dict(requested=enabled, above_normal=False, timer_1ms=False)
    previous = None
    if enabled and os.name == 'nt':
        import ctypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.GetCurrentProcess.restype = ctypes.c_void_p
        kernel.GetPriorityClass.argtypes = [ctypes.c_void_p]
        kernel.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        handle = kernel.GetCurrentProcess()
        previous = kernel.GetPriorityClass(handle)
        status['above_normal'] = bool(kernel.SetPriorityClass(handle, 0x8000))
        timer = ctypes.WinDLL('winmm')
        status['timer_1ms'] = timer.timeBeginPeriod(1) == 0
    try:
        yield status
    finally:
        if previous is not None:
            if status['timer_1ms']:
                timer.timeEndPeriod(1)
            if previous:
                kernel.SetPriorityClass(handle, previous)


def send(source, destination, port, hz, seconds, output, interface=None,
         spin_us=0, tune_windows=False):
    source_ip = ipaddress.IPv4Address(source)
    destination_ip = ipaddress.IPv4Address(destination)
    if not source_ip.is_private or not destination_ip.is_private:
        raise ValueError('Stimulus is limited to local/private addresses')
    if not 1 <= hz <= 600 or not 0.1 <= seconds <= 25 or not 1024 <= port <= 65535:
        raise ValueError('Invalid rate, duration or port budget')
    if not 0 <= spin_us <= 1000:
        raise ValueError('Final busy wait is limited to one millisecond per slot')
    output = Path(output)
    output.mkdir(exist_ok=False, parents=True)
    period = 1_000_000_000 / hz
    slots = int(hz * seconds)
    records = []
    skipped = 0
    error = None
    started_utc_ns = time.time_ns()
    with timing_scope(tune_windows) as timing, socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, 1)
        if interface is not None:
            # Windows IP_UNICAST_IF takes the index in network byte order.
            sock.setsockopt(socket.IPPROTO_IP, 31, struct.pack('!I', interface))
        sock.bind((source, 0))
        local_endpoint = sock.getsockname()
        start = time.perf_counter_ns() + 100_000_000
        slot = 0
        while slot < slots:
            target = start + round(slot * period)
            remaining = target - time.perf_counter_ns()
            if remaining > spin_us * 1000:
                time.sleep((remaining - spin_us * 1000) / 1_000_000_000)
            while time.perf_counter_ns() < target:
                pass
            before = time.perf_counter_ns()
            # Skip missed slots instead of injecting a catch-up burst.
            due_slot = int((before - start) / period)
            if due_slot > slot:
                skipped += min(due_slot, slots) - slot
                slot = due_slot
                if slot >= slots:
                    break
                target = start + round(slot * period)
            payload = struct.pack('<8sQQQ', b'CSI300V1', slot, before, target) + bytes(224)
            try:
                size = sock.sendto(payload, (destination, port))
                after = time.perf_counter_ns()
                records.append((slot, target, before, after, size))
            except OSError as exc:
                error = dict(type=type(exc).__name__, message=str(exc))
                break
            slot += 1
        elapsed_ns = time.perf_counter_ns() - start
    with (output / 'sends.csv').open('x', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(('slot', 'target_ns', 'before_send_ns', 'after_send_ns', 'bytes'))
        writer.writerows(records)
    intervals = [(b[2] - a[2]) / 1e6 for a, b in zip(records, records[1:])]
    intervals.sort()
    send_latency = sorted((r[3] - r[2]) / 1e6 for r in records)
    lateness = sorted((r[2] - r[1]) / 1e6 for r in records)
    def quantile(values, fraction):
        return values[round((len(values) - 1) * fraction)] if values else None
    span = records[-1][2] - records[0][2] if len(records) > 1 else 0
    summary = dict(schema=1, source=source, destination=destination, port=port,
                   interface_index=interface, local_endpoint=local_endpoint,
                   timing_tuning=timing, final_spin_us=spin_us,
                   requested_hz=hz, requested_seconds=seconds, scheduled_slots=slots,
                   started_utc_ns=started_utc_ns, elapsed_seconds=elapsed_ns / 1e9,
                   send_calls_succeeded=len(records), skipped_late_slots=skipped,
                   schedule_complete=len(records) == slots and skipped == 0 and error is None,
                   error=error, payload_bytes=256,
                   send_call_rate_hz=(len(records) - 1) * 1e9 / span if span else None,
                   interval_ms=dict(min=min(intervals) if intervals else None,
                                    p50=quantile(intervals, .5), p95=quantile(intervals, .95),
                                    p99=quantile(intervals, .99), max=max(intervals) if intervals else None),
                   lateness_ms=dict(p50=quantile(lateness, .5), p99=quantile(lateness, .99)),
                   send_latency_ms=dict(p50=quantile(send_latency, .5),
                                        p99=quantile(send_latency, .99),
                                        max=max(send_latency) if send_latency else None),
                   limitation='Socket send completion is not proof of wireless transmission or CSI reception')
    (output / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--destination', required=True)
    parser.add_argument('--port', type=int, default=39031)
    parser.add_argument('--hz', type=float, default=300)
    parser.add_argument('--seconds', type=float, default=10)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--interface', type=int)
    parser.add_argument('--spin-us', type=int, default=0)
    parser.add_argument('--tune-windows', action='store_true')
    args = parser.parse_args()
    result = send(args.source, args.destination, args.port, args.hz, args.seconds,
                  args.output, args.interface, args.spin_us, args.tune_windows)
    print(json.dumps(result))
    return 1 if result['error'] else 0 if result['schedule_complete'] else 7


if __name__ == '__main__':
    raise SystemExit(main())
