"""Linux tests of the production guard's local TX lease, using mock nexutil.

Usage: python3 test_tx_lease.py /path/to/router_guard /new/output/directory
The normal case runs for 68 real seconds, crossing the initial 60-second lease
with unchanged production 10-second renewals. No radio, board or SDK access.
"""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
import json
import math
from pathlib import Path
import signal
import struct
import subprocess
import sys
import time


MAGIC = 0x314C5854
TOKEN = 0x3C246917


def mock_command():
    folder = Path.cwd()
    state_file = folder / 'mock-state.json'
    state = json.loads(state_file.read_text()) if state_file.exists() else dict(
        configured=False, running=False, configurations=0, starts=0, stops=0,
        frees=0, sequence=0, renewals=0, token=TOKEN, error=0, lease_queries=0)
    scenario = (folder / 'scenario').read_text().strip()
    operation = sys.argv[2]
    at = time.monotonic()
    elapsed = at - state.get('started_at', at)
    record = dict(operation=operation, at=at)
    output, code, delay = '', 0, 0
    if state['running'] and at >= state['expires_at']:
        state.update(running=False, error=3)
    if operation == '-s429':
        assert not state['configured'], state
        assert sys.argv[3:6] == ['-b', '-l64', '-v']
        state.update(configured=True, configurations=state['configurations'] + 1)
        if scenario == 'stop_during_configure':
            (folder / 'stop.request').touch()
    elif operation == '-s430':
        assert state['configured'] and not state['running'], state
        state.update(running=True, starts=state['starts'] + 1,
                     started_at=at, expires_at=at + 60, initial_expires_at=at + 60)
        if scenario == 'start_error':
            code = 9  # Submission happened, but the userspace result failed.
    elif operation == '-s434':
        assert sys.argv[3:6] == ['-b', '-l12', '-v']
        magic, token, sequence = struct.unpack('<3I', base64.b64decode(sys.argv[6], validate=True))
        assert magic == MAGIC and token == TOKEN and sequence == state['sequence'] + 1
        assert state['configured'] and state['running'] and at < state['expires_at'], state
        record['sequence'] = sequence
        if scenario == 'renew_command_error':
            code = 9
        else:
            state.update(sequence=sequence, renewals=state['renewals'] + 1,
                         expires_at=at + 60)
            if scenario == 'renew_timeout_after_accept':
                delay = 4
    elif operation == '-g435':
        assert sys.argv[3:] == ['-l32', '-R'] and state['configured'], state
        state['lease_queries'] += 1
        if elapsed >= 1 and state['running']:
            if scenario == 'lease_expired':
                state.update(running=False, error=3, expires_at=at)
            elif scenario == 'firmware_error':
                state.update(running=False, error=4)
            elif scenario == 'unexpected_stop':
                state['running'] = False
        remaining = max(0, math.ceil((state.get('expires_at', at) - at) * 1000)) if state['running'] else 0
        token = TOKEN + int(scenario == 'identity_mismatch' and elapsed >= 1)
        seq = state['sequence'] + int(scenario == 'renew_ack_mismatch' and state['sequence'] > 0)
        words = [MAGIC, 1, token, seq, remaining, int(state['running']), state['error'], state['renewals']]
        output = base64.b64encode(struct.pack('<8I', *words)).decode()
        record.update(token=token, running=int(state['running']), remaining_ms=remaining,
                      sequence=seq, error=state['error'])
        if scenario == 'invalid_status' and elapsed >= 1:
            output = 'invalid-status'
        if scenario == 'status_timeout' and elapsed >= 1:
            delay = 4
        if elapsed >= 1 and scenario in ('stop_request', 'stop_unproven', 'stop_timeout_but_stopped'):
            (folder / 'stop.request').touch()
        if elapsed >= 1 and scenario == 'pause_request':
            (folder / 'pause.seconds').write_text('20\n')
        if elapsed >= 1 and scenario == 'guard_signal':
            import os
            os.kill(int((folder / 'guard.pid').read_text()), signal.SIGTERM)
    elif operation == '-g433':
        assert state['configured'] and state['running'], state
        submitted = int(elapsed * 300)
        words = [0x3158544E, 1, 300, max(0, int((state['expires_at'] - at) * 300)),
                 submitted, 0, state['error'], 100, 3, int(at * 1e6) & 0xFFFFFFFF,
                 int(at * 1e6) & 0xFFFFFFFF, 1]
        output = base64.b64encode(struct.pack('<12I', *words)).decode()
    elif operation == '-s431':
        state['stops'] += 1
        if scenario != 'stop_unproven':
            state['running'] = False
        if scenario == 'stop_timeout_but_stopped':
            delay = 4
    elif operation == '-s432':
        assert state['configured'] and not state['running'], state
        state.update(configured=False, frees=state['frees'] + 1)
    else:
        raise AssertionError(operation)
    record['exit'] = code
    with (folder / 'operations.jsonl').open('a') as log:
        log.write(json.dumps(record) + '\n')
    state_file.write_text(json.dumps(state))
    if delay:
        time.sleep(delay)
    if output:
        print(output)
    return code


def await_final(folder, seconds):
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        try:
            return json.loads((folder / 'guard-final.json').read_text())
        except (OSError, ValueError):
            time.sleep(.05)
    raise AssertionError('guard did not stop and restore: ' + str(folder))


def run_scenario(root, guard, scenario):
    folder = root / scenario
    folder.mkdir()
    (folder / 'armed').touch()
    (folder / 'tx.lease').touch()
    if scenario == 'autostart':
        (folder / 'continuous').touch()
    (folder / 'scenario').write_text(scenario)
    fake = folder / 'nexutil'
    fake.write_text('#!' + sys.executable + '\n' + Path(__file__).read_text())
    fake.chmod(0o755)
    (folder / 'run.params').write_text('mock-lease-parameters\n')
    (folder / 'restore.sh').write_text('touch restored\nrm -f armed\n')
    duration = 68 if scenario in ('continuous', 'autostart') else 3 if scenario == 'guard_deadline' else 25
    launched = subprocess.run([guard, 'tx', str(folder), '0' if scenario == 'autostart' else str(duration), '127.0.0.1',
                               '39033', 'lo'], check=True, capture_output=True, text=True)
    json.loads(launched.stdout)['guard_pid']
    try:
        if scenario == 'autostart':
            time.sleep(duration)
            assert not (folder / 'guard-final.json').exists()
            (folder / 'stop.request').touch()
        final = await_final(folder, duration + 15)
    finally:
        (folder / 'stop.request').touch()
    state = json.loads((folder / 'mock-state.json').read_text())
    operations = [json.loads(line) for line in (folder / 'operations.jsonl').read_text().splitlines()]
    events = (folder / 'guard.log').read_text()
    assert final['restore_exit'] == 0 and (folder / 'restored').exists(), final
    assert not (folder / 'armed').exists()
    assert final['generations'] == state['configurations'] == 1, (final, state)
    assert state['starts'] == int(scenario != 'stop_during_configure'), state
    assert state['stops'] == 1, state
    assert final['completed_TX_jobs'] == 0, final
    assert len(list(folder.glob('tx-*.status'))) <= 2
    assert sum(p.stat().st_size for p in folder.glob('guard*.log')) < 4096
    assert 'TX lease end reason=' in events and 'stop_proven=' in events
    stop_index = next(i for i, item in enumerate(operations) if item['operation'] == '-s431')
    assert operations[stop_index + 1]['operation'] == '-g435', operations[stop_index:]
    unproven = scenario in ('identity_mismatch', 'invalid_status', 'status_timeout', 'stop_unproven')
    assert state['frees'] == int(not unproven), state
    assert (folder / 'tx.released').exists() == bool(state['frees'])
    if not unproven:
        assert operations[stop_index + 1]['running'] == 0
        assert operations[stop_index + 2]['operation'] == '-s432'
        assert not state['configured']
    normal = scenario in ('continuous', 'autostart', 'guard_deadline', 'stop_request',
                          'stop_during_configure', 'pause_request', 'guard_signal', 'stop_timeout_but_stopped')
    assert final['guard_fault'] == int(not normal), (scenario, final, events)
    result = dict(final=final, starts=state['starts'], renew_commands=state['renewals'],
                  stop_proven=not unproven, frees=state['frees'])
    if scenario in ('continuous', 'autostart'):
        assert final['TX_renewals'] >= 6 and final['TX_stop_reason'] == ('stop_request' if scenario == 'autostart' else 'guard_deadline'), final
        assert operations[stop_index]['at'] > state['initial_expires_at'] + 5
        renews = [item for item in operations if item['operation'] == '-s434']
        assert [item['sequence'] for item in renews] == list(range(1, len(renews) + 1))
        assert all(9.8 <= b['at'] - a['at'] < 12 for a, b in zip(renews, renews[1:])), renews
        assert all(item.get('remaining_ms', 1) > 0 for item in operations[:stop_index]
                   if item['operation'] == '-g435' and item['running'])
        result['same_context_seconds'] = operations[stop_index]['at'] - state['started_at']
    elif scenario.startswith('renew_'):
        assert len([item for item in operations if item['operation'] == '-s434']) == 1
        assert final['TX_renewal_failures'] == 1 and final['TX_renewals'] == 0, final
    elif scenario == 'stop_timeout_but_stopped':
        assert 'stop_exit=143' in events or 'stop_exit=137' in events, events
        assert 'stop_proven=1' in events
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('guard')
    parser.add_argument('output')
    args = parser.parse_args()
    root = Path(args.output).resolve()
    root.mkdir()
    guard = str(Path(args.guard).resolve())
    scenarios = ('continuous', 'autostart', 'guard_deadline', 'stop_request', 'stop_during_configure',
                 'pause_request', 'guard_signal', 'renew_command_error',
                 'renew_timeout_after_accept', 'renew_ack_mismatch', 'identity_mismatch',
                 'lease_expired', 'firmware_error', 'unexpected_stop', 'invalid_status',
                 'status_timeout', 'stop_unproven', 'stop_timeout_but_stopped', 'start_error')
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {scenario: pool.submit(run_scenario, root, guard, scenario) for scenario in scenarios}
        results = {scenario: future.result() for scenario, future in futures.items()}
    result = dict(mock_only=True, hardware_access=False, production_renewal_seconds=10, results=results)
    (root / 'result.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result))


if __name__ == '__main__':
    if Path(sys.argv[0]).name == 'nexutil':
        sys.exit(mock_command())
    main()
