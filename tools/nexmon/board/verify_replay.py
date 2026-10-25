"""Differential test of native ingress against frozen Python grid and CSI math.

Only offline captures are read; no router, SDK, model or board is contacted.
Explicit gains here are synthetic verification factors, NOT calibration.
"""
import argparse
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

import numpy as np

HOST = Path(__file__).resolve().parents[1] / 'host'
sys.path.insert(0, str(HOST))
from audit_three_receivers import read_receiver
from native_carriers import select_packed, decode_selected
from map_node_windows import HT20_NG2


def verify(binary, evidence, scratch):
    rows = []
    gains = (1.0, 2.0, 3.0)
    with tempfile.TemporaryDirectory(prefix='native-ingress-', dir=scratch) as folder:
        folder = Path(folder)
        for run, expected in ((1, 120), (2, 117), (3, 108)):
            frozen = json.loads((evidence / f'run300-{run}-joint.json').read_text())
            paths = [evidence / name / f'run300-{run}.pcap' for name in ('rx1', 'rx2', 'rx3')]
            nodes = [read_receiver(p, f'rx{r+1}', f'run{run}', 'f0:2f:74:39:45:6c', 0xd0a1)
                     for r, p in enumerate(paths)]
            fits = [n.state['startup'][0] for n in nodes]
            shifts = frozen['joint_grid']['fixed_integer_slot_shifts']
            cells = []
            for node, fit, shift in zip(nodes, fits, shifts):
                cells.append({(target-fit['phase_scaled'])//1_000_000+shift: obs
                    for w in node.windows for target, obs in zip(w.target_scaled, w.observations)})
            reference_bytes = None
            for mode in ('roundrobin', 'serial', 'chunked'):
                wire, report = folder/f'{run}-{mode}.bin', folder/f'{run}-{mode}.json'
                cmd = [str(binary), '--session', f'run{run}', '--source-mac', 'f0:2f:74:39:45:6c',
                    '--channel', '0xd0a1', '--gains', *map(str, gains), '--pcaps', *map(str, paths),
                    '--interleave', mode, '--output', str(wire), '--report', str(report)]
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                actual = json.loads(report.read_text())
                assert actual['valid_windows'] == expected
                assert actual['complete_windows'] == frozen['joint_grid']['complete_windows']
                assert actual['common_events'] == frozen['common_packets']['common_identities']
                assert actual['decisions'] == [{k:w[k] for k in ('start_reference_slot', 'valid')}
                                               for w in frozen['joint_grid']['windows']]
                assert actual['slot_shifts'] == shifts
                assert actual['emitted_before_eof']
                for r in range(3):
                    assert actual['nodes'][r]['phase_scaled'] == fits[r]['phase_scaled']
                    assert actual['nodes'][r]['calibration_end_us'] == fits[r]['calibration_end_us']
                data = wire.read_bytes()
                assert len(data) == expected*86432
                if reference_bytes is not None:
                    assert data == reference_bytes, 'Arrival interleaving changed output bytes'
                reference_bytes = data
                for i, window in enumerate(actual['windows']):
                    start = window['start_reference_slot']
                    ids = [[cells[r][start+t].index for t in range(20)] for r in range(3)]
                    assert window['event_indices'] == ids
                    reference = np.empty((3,3,20,30), dtype='complex128')
                    for r in range(3):
                        for t, index in enumerate(ids[r]):
                            event = nodes[r].events[index]
                            reference[r,:,t,:] = decode_selected(select_packed(
                                event.words, HT20_NG2, event.original_words))*gains[r]
                    offset = i*86432
                    assert struct.unpack_from('<8sIIQQ', data, offset) == (b'PIWCSI2\0',2,86400,i+1,0)
                    native = np.frombuffer(data, dtype='<c16', count=5400, offset=offset+32).reshape(3,3,20,30)
                    assert np.array_equal(native, reference), 'Native decoded/mapped/gained CSI differs'
                rows.append(dict(run=run, interleave=mode, valid_windows=expected,
                    complete_windows=actual['complete_windows'], exact_complex_values=expected*5400,
                    first_ready_after_packets=actual['first_ready_after_packets'],
                    total_packets=actual['packets'], native_stdout=result.stdout.strip(),
                    all_window_indices_and_values_equal=True, byte_identical_across_interleavings=True))
    return dict(schema=1, offline_only=True, native_cpp17=True, candidate_test_gains=gains,
        physical_power_calibrated=False, model_or_sdk_or_protocol_changed=False,
        board_execution_performed=False, checks=rows)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args=parser.parse_args()
    result=verify(args.binary.resolve(), args.evidence.resolve(), args.scratch.resolve())
    with args.output.open('x', encoding='utf-8') as f:
        json.dump(result, f, indent=2, allow_nan=False)
    print(json.dumps(dict(replays=len(result['checks']), all_passed=True)))
