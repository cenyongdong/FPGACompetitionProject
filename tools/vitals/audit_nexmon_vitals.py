"""Offline eligibility audit of recorded CSI for the unchanged vitals module.

Uses the acquisition branch's existing event pairing and first-valid dedup.
Never acquires data, resamples, relabels a clock, or produces a heart-rate claim.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from scipy import signal

HOST = Path(__file__).resolve().parents[1] / 'nexmon' / 'host'
sys.path.insert(0, str(HOST))
from diagnose_metadata import decode, packets
from native_carriers import decode_selected
from stream_node import NodeStream
from signal_fixtures import write_csv

CARRIERS = [5, 11, 17, 23]  # Existing diagnostic profile; not HR-sensitive selection.
PAIRS = [(0, 1), (0, 2), (1, 2), (0, 1)]


def save(path, value):
    with path.open('x', encoding='utf-8') as out:
        json.dump(value, out, indent=2, ensure_ascii=False, allow_nan=False)


def describe(values):
    a = np.asarray(values, dtype=float)
    if not a.size:
        return None
    return dict(count=int(a.size), min=float(a.min()), p50=float(np.median(a)),
                p95=float(np.percentile(a, 95)), p99=float(np.percentile(a, 99)), max=float(a.max()))


def load_segment(pcap):
    """Replay one archived capture and retain its longest continuous RX-clock segment."""
    if not pcap.is_file() or pcap.stat().st_size > 32 * 1024 * 1024:
        raise ValueError('Require an archived PCAP within the existing 32MiB capture budget')
    identity = None
    for _, port, payload in packets(pcap):
        if port == 5501:
            d = decode(payload)
            identity = d['mac'], d['channel']
            break
    if identity is None:
        raise ValueError('This audit needs paired NMD records; legacy import must remain explicit')
    stream = NodeStream(*identity)
    events = []
    stream.on_event = events.append
    for stamp, port, payload in packets(pcap):
        stream.feed(stamp, port, payload)
    state = stream.finish()
    kept = [e for e in events if e.decision == 'keep']
    if not kept:
        raise ValueError('No first-valid complete three-core receptions')
    groups = defaultdict(list)
    for e in kept:
        groups[e.segment].append(e)
    # Do not join captures or clock segments into a longer physiological window.
    selected = max(groups.values(), key=lambda g: g[-1].time_us - g[0].time_us)
    return selected, state, groups


def audit(pcap, output, executable):
    output.mkdir(parents=True, exist_ok=False)
    selected, state, groups = load_segment(pcap)
    iq = decode_selected(np.asarray([e.words for e in selected])[:, :, CARRIERS])
    pairs = np.stack([iq[:, [a, b], ch] for ch, (a, b) in enumerate(PAIRS)], axis=1)
    finite = bool(np.isfinite(pairs).all())
    if not finite:
        raise ValueError('Non-finite selected I/Q; preserve source and stop case')
    scale = np.maximum(np.abs(pairs.real), np.abs(pairs.imag))
    if (scale < 1e-12).any():
        raise ValueError('Zero selected antenna value; phase is undefined')
    normalized = pairs / scale
    phase = np.angle(normalized[:, :, 0] * normalized[:, :, 1].conj())
    # Circular steps, before temporal unwrapping, with no smoothing or repair.
    steps = np.abs(np.angle(np.exp(1j * np.diff(phase, axis=0))))
    unwrapped = np.unwrap(phase, axis=0)
    detrended = signal.detrend(unwrapped, axis=0, type='linear')
    phase_rows = []
    for ch, pair in enumerate(PAIRS):
        phase_rows.append(dict(feature=ch, fft_index=CARRIERS[ch], rx_pair=pair,
            adjacent_phase_step_rad=describe(steps[:, ch]),
            steps_over_reference_0_25_rad=int((steps[:, ch] > .25).sum()),
            fraction_over_reference_0_25_rad=float(np.mean(steps[:, ch] > .25)),
            detrended_rms_rad=float(np.sqrt(np.mean(detrended[:, ch] ** 2)))))
    tids = {e.meta['tid'] for e in selected}
    if len(tids) != 1:
        raise ValueError('Different QoS sequence spaces cannot share the strict CSV sequence field')
    sequences = []
    previous = extended = selected[0].meta['seq'] >> 4
    for i, e in enumerate(selected):
        now = e.meta['seq'] >> 4
        if i:
            delta = (now - previous) & 4095
            if not 0 < delta < 2048:
                raise ValueError('Ambiguous source Wi-Fi sequence progression')
            extended += delta
        sequences.append(extended)
        previous = now
    times = np.asarray([round((e.meta['time'] - selected[0].meta['time']) * 1e9)
                        for e in selected], dtype=np.uint64)
    fixture = dict(pairs=pairs, times=times, sequences=np.asarray(sequences, dtype=np.uint64),
        valid=np.ones(len(selected), dtype=np.uint8), origin='real_capture',
        clock='unknown_arrival', rate=50,
        clock_evidence='PCAP arrival time only. 50Hz is the unchanged target, not the observed rate. '
            'Original Wi-Fi sequence retained after first-valid dedup; no interpolation or relabeling.')
    csv = output / 'input.csv'
    write_csv(csv, fixture)
    result_path = output / 'native-result.json'
    process = subprocess.run([str(executable), '--input', str(csv), '--output', str(result_path)],
                             capture_output=True, text=True, timeout=30)
    save(output / 'native-process.json', dict(exit_code=process.returncode,
        stdout=process.stdout, stderr=process.stderr))
    if process.returncode:
        raise RuntimeError('Native offline run failed; inspect preserved process result')
    native = json.loads(result_path.read_text())
    analyzed = min(len(selected), 2000)
    result = dict(source=str(pcap.resolve()), source_sha256=hashlib.sha256(pcap.read_bytes()).hexdigest(),
        counts=state['counts'], clock_segment_resets=state['clock_segment_resets'],
        segment_rows=[dict(segment=key, first_valid_events=len(g),
            relative_rx_span_s=(g[-1].time_us-g[0].time_us)/1e6) for key, g in groups.items()],
        selected_segment=selected[0].segment, selected_first_valid_events=len(selected),
        selected_relative_rx_span_s=(selected[-1].time_us-selected[0].time_us)/1e6,
        pcap_arrival_span_s=float(times[-1])/1e9,
        relative_rx_interval_ms=describe(np.diff([e.time_us for e in selected])/1000),
        iq_finite=finite, phase_diagnostics=phase_rows,
        native_analyzed_samples=native['quality']['samples'],
        native_first_window_actual_arrival_span_s=float(times[analyzed-1])/1e9,
        native_status=native['status'], native_reasons=native['reasons'],
        heart=native['heart'], breath=native['breath'],
        measured_coverage_reaches_40s=bool((selected[-1].time_us-selected[0].time_us)/1e6
            + float(np.median(np.diff([e.time_us for e in selected])))/1e6 >= 40),
        heart_ground_truth_available=False,
        physiology_detection_validated=False,
        limitations=['Four carriers/pairs are diagnostic selections, not validated HR-sensitive channels.',
            'Wi-Fi sequence gaps do not by themselves prove sampling loss; other source traffic can consume sequence values.',
            'Phase step comparisons use the original 0.25rad reference threshold but are not a full 40s quality verdict.',
            'The native reader takes the first 2000 rows at the unchanged 50Hz profile; row count is not duration.',
            'No padding, interpolation, clock relabeling, segment concatenation, threshold changes, or model/board execution.'])
    save(output / 'audit.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pcap', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--executable', type=Path, required=True)
    args = parser.parse_args()
    r = audit(args.pcap, args.output, args.executable.resolve())
    print(json.dumps({k: r[k] for k in ('selected_first_valid_events', 'selected_relative_rx_span_s',
        'native_status', 'native_reasons', 'heart', 'breath')}, indent=2))
