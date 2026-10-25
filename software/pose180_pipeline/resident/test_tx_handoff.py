"""Linux tests of the real guard with a finite, stateful mock nexutil.

Usage: python3 test_tx_handoff.py /path/to/router_guard /new/output/directory
No radio firmware, SDK, board access or parameter changes. Mock jobs finish in
about one second; their status counters retain the finite-job lifecycle.
"""
import argparse
import base64
import json
import math
from pathlib import Path
import statistics
import struct
import subprocess
import sys
import time


def mock_command():
    """Run as ./nexutil by the unmodified command runner in router_guard."""
    folder = Path.cwd()
    path = folder / 'mock-state.json'
    state = json.loads(path.read_text()) if path.exists() else {
        'configured': False, 'started': False, 'starts': 0, 'stops': 0,
        'configurations': 0, 'last_running': None, 'queries': 0,
    }
    scenario = (folder / 'scenario').read_text().strip()
    operation = sys.argv[2]
    at = time.monotonic()
    record = dict(operation=operation, at=at, generation=state['starts'])
    output, code = '', 0
    if operation == '-s429':
        # Reject reconfiguration of a live context; 432 must have freed it.
        assert not state['configured'], state
        assert len(sys.argv) == 7 and sys.argv[3:6] == ['-b', '-l64', '-v']
        state['configured'] = True
        state['configurations'] += 1
        if scenario == 'stop_during_configure':
            (folder / 'stop.request').touch()
    elif operation == '-s430':
        assert len(sys.argv) == 3 and state['configured'] and not state['started'], state
        state['starts'] += 1
        state['started'] = True
        state['start_time'] = at
        state['finish_time'] = at + .95
        state['queries'] = 0
        record['generation'] = state['starts']
        if scenario == 'start_error':
            code = 9
    elif operation == '-s432':
        # Unlike the old mock, this matches actual firmware: a double free is
        # an error and therefore cannot masquerade as a clean guard shutdown.
        if not state['configured']:
            code = 8
        else:
            state['configured'] = state['started'] = False
            state['stops'] += 1
    elif operation == '-g433':
        assert state['configured'] and state['started'], state
        state['queries'] += 1
        remaining = max(0, math.ceil((state['finish_time'] - at) * 300))
        running = int(at < state['finish_time'])
        error = 7 if scenario == 'firmware_error' and state['starts'] == 2 else 0
        # Advertise zero remaining before the final running flag changes. The
        # guard must still wait for a fresh completed status, never start from
        # elapsed host time or remaining-count estimates alone.
        if scenario == 'handoff' and remaining <= 60:
            remaining = 0
        if scenario == 'stop_mid_job':
            (folder / 'stop.request').touch()
        words = [0x3158544e, running, 300, remaining, 18000 - remaining,
                 0, error, 100, 1, 2000000, 2000500, 1]
        output = base64.b64encode(struct.pack('<12I', *words)).decode()
        record.update(running=running, remaining=remaining, error=error)
        state['last_running'] = running
        if scenario == 'invalid_status':
            output = 'mock-malformed-native-status'
        elif scenario == 'query_error':
            output, code = 'mock-command-error', 9
        elif not running and state['starts'] == 2:
            (folder / 'stop.request').touch()
    else:
        raise AssertionError(operation)
    record['exit'] = code
    with (folder / 'operations.jsonl').open('a') as log:
        log.write(json.dumps(record) + '\n')
    path.write_text(json.dumps(state))
    if output:
        print(output)
    return code


def await_final(folder, timeout=12):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            return json.loads((folder / 'guard-final.json').read_text())
        except (OSError, ValueError):
            time.sleep(.025)
    raise AssertionError('Guard did not restore and finish: ' + str(folder))


def run_scenario(root, guard, scenario):
    folder = root / scenario
    folder.mkdir()
    (folder / 'scenario').write_text(scenario)
    (folder / 'armed').touch()
    # Copy this very test as the command executable, avoiding dependencies on
    # temporary import paths and allowing each command to have its own process.
    fake = folder / 'nexutil'
    fake.write_text('#!' + sys.executable + '\n' + Path(__file__).read_text())
    fake.chmod(0o755)
    (folder / 'run.params').write_text('mock-finite-parameters\n')
    (folder / 'restore.sh').write_text('touch restored\nrm -f armed\n')
    # Exercise rotation without growing the live or retained diagnostic log.
    if scenario == 'handoff':
        (folder / 'guard.log').write_text('x' * 65536)
    launched = subprocess.run([guard, 'tx', str(folder), '8', '127.0.0.1',
                               '39033', 'lo'], check=True, capture_output=True, text=True)
    json.loads(launched.stdout)['guard_pid']
    try:
        final = await_final(folder)
    finally:
        (folder / 'stop.request').touch()
    state = json.loads((folder / 'mock-state.json').read_text())
    operations = [json.loads(line) for line in (folder / 'operations.jsonl').read_text().splitlines()]
    events = (folder / 'guard.log').read_text()
    assert final['restore_exit'] == 0 and (folder / 'restored').exists(), final
    assert not (folder / 'armed').exists() and not state['configured'], state
    assert len(list(folder.glob('tx-*.status'))) <= 4
    assert sum(p.stat().st_size for p in folder.glob('guard*.log')) <= 2 * 65536 + 2048
    assert state['stops'] == state['configurations'], (state, operations)
    assert not any(item['operation'] == '-s432' and item['exit'] for item in operations)
    assert 'TX end reason=' in events and 'stop_ms=' in events
    result = dict(final=final, starts=state['starts'], frees=state['stops'])
    if scenario == 'handoff':
        assert final['guard_fault'] == 0 and final['completed_TX_jobs'] == 2, final
        assert state['starts'] == state['configurations'] == 2, state
        first_queries = [item for item in operations if item['generation'] == 1 and item['operation'] == '-g433']
        complete = first_queries[-1]
        assert complete['running'] == 0 and complete['remaining'] == 0
        assert any(item['running'] and not item['remaining'] for item in first_queries)
        second_start = next(item for item in operations if item['operation'] == '-s430' and item['generation'] == 2)
        assert second_start['at'] > complete['at']
        gaps = [(later['at'] - earlier['at'], earlier['remaining'])
                for earlier, later in zip(first_queries, first_queries[1:])]
        steady = [gap for gap, remaining in gaps if remaining > 150]
        tail = [gap for gap, remaining in gaps if remaining <= 150]
        assert steady and len(tail) >= 3, gaps
        # Relative timing is robust to command/interpreter overhead; this
        # catches accidentally retaining the old 250 ms tail wait.
        assert statistics.median(tail) < statistics.median(steady) * .8, gaps
        assert 'completion_to_start_ms=' in events and 'tail_polls=' in events
        assert (folder / 'guard.previous.log').stat().st_size == 65536
        result.update(steady_poll_median_ms=statistics.median(steady) * 1000,
                      tail_poll_median_ms=statistics.median(tail) * 1000,
                      completion_observed_to_next_start_ms=(second_start['at'] - complete['at']) * 1000,
                      zero_remaining_did_not_start_early=True)
    elif scenario == 'firmware_error':
        assert final['guard_fault'] == 1 and final['completed_TX_jobs'] == 1, final
        assert state['starts'] == 2 and 'reason=firmware_error' in events
    elif scenario in ('invalid_status', 'query_error', 'start_error'):
        assert final['guard_fault'] == 1 and final['completed_TX_jobs'] == 0, final
        assert state['starts'] == 1, state
        reason = dict(invalid_status='status_invalid', query_error='status_command_failed', start_error='start_failed')[scenario]
        assert 'reason=' + reason in events
    elif scenario in ('stop_mid_job', 'stop_during_configure'):
        assert final['guard_fault'] == 0 and final['completed_TX_jobs'] == 0, final
        assert state['starts'] == (scenario == 'stop_mid_job'), state
        assert 'reason=guard_stop' in events
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('guard')
    parser.add_argument('output')
    args = parser.parse_args()
    root = Path(args.output).resolve()
    root.mkdir()
    guard = str(Path(args.guard).resolve())
    results = {scenario: run_scenario(root, guard, scenario) for scenario in (
        'handoff', 'firmware_error', 'invalid_status', 'query_error',
        'start_error', 'stop_mid_job', 'stop_during_configure')}
    result = dict(mock_only=True, hardware_access=False, results=results)
    (root / 'result.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result))


if __name__ == '__main__':
    if Path(sys.argv[0]).name == 'nexutil':
        sys.exit(mock_command())
    main()
