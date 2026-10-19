"""Export complete RX-core events for one node, without creating model inputs.

Repeated identities are retained and flagged. An event is a contiguous complete
set of configured core reports; it is not proof of a distinct RF training field.
"""
import argparse
import collections
import json
from pathlib import Path

import numpy as np

from csi_verify import parse_payload, pcap_udp, unpack_acphy


def assemble(records, nfft, cores, source_mac, chip=106):
    required = set(cores)
    if len(required) != len(cores) or not required:
        raise ValueError('Core IDs must be nonempty and unique')
    events, pending = [], {}
    current = None
    count = 0
    for timestamp, payload in records:
        count += 1
        item = parse_payload(payload, nfft)
        if (item['mac'] != source_mac.lower() or item['chip'] != chip or
                item['stream'] != 0 or item['core'] not in required):
            raise ValueError('Unexpected node/core/stream/chip identity')
        key = (item['mac'], item['sequence_control'], item['chanspec'], item['stream'])
        if pending and (key != current or item['core'] in pending):
            raise ValueError('Incomplete or interleaved event; inspect original PCAP')
        current = key
        pending[item['core']] = (timestamp, item)
        if set(pending) == required:
            events.append((key, [pending[c] for c in cores]))
            pending = {}
    if pending:
        raise ValueError('Incomplete final event')
    if not events:
        raise ValueError('No complete node events')
    return events, count


def export(pcap, output, nfft, cores, source_mac):
    output = Path(output)
    if output.exists():
        raise ValueError('Refusing to overwrite an export')
    events, count = assemble(pcap_udp(pcap), nfft, cores, source_mac)
    words = np.asarray([[entry[1]['words'] for entry in values] for _, values in events], dtype='<u4')
    decoded = np.asarray([[unpack_acphy(entry[1]['words']) for entry in values]
                          for _, values in events], dtype='<c16')
    if not np.isfinite(decoded).all() or np.any(~np.any(decoded != 0, axis=2)):
        raise ValueError('Non-finite or all-zero core report')
    arrivals = np.asarray([[entry[0] for entry in values] for _, values in events], dtype='<f8')
    starts = arrivals.min(axis=1)
    seq = np.asarray([key[1] for key, _ in events], dtype='<u2')
    channels = np.asarray([key[2] for key, _ in events], dtype='<u2')
    # Diagnostic horizon from the previous same-key event; retain every event.
    # The strict verifier instead anchors its group horizon at the first record.
    seen = {}
    repeats = []
    for (key, _), timestamp in zip(events, starts):
        repeats.append(bool(key in seen and (timestamp - seen[key]) * 1000 <= 20))
        seen[key] = timestamp
    relative = starts - starts[0]
    bins = collections.defaultdict(list)
    for i, timestamp in enumerate(relative):
        bins[int(timestamp)].append(i)
    intervals = np.diff(starts) * 1000
    windows = (starts[19:] - starts[:-19]) * 1000 if len(events) >= 20 else []
    def stats(values):
        return dict(zip(('min', 'p50', 'p95', 'p99', 'max'),
                        (float(x) for x in np.quantile(values, [0, .5, .95, .99, 1])))) if len(values) else None
    report = dict(schema=1, model_ready=False, receiver_nodes=1,
                  event_shape=list(words.shape), packed_dtype='uint32', decoded_dtype='complex128, unscaled',
                  csi_records=count, complete_contiguous_core_events=len(events),
                  repeated_identity_events_20ms=sum(repeats), source_mac=source_mac,
                  selected_cores=cores, stream=0, nfft=nfft,
                  arrival_interval_ms=stats(intervals), twenty_event_first_to_last_ms=stats(windows),
                  per_second=[dict(second=k, events=len(v), distinct_sequence_controls=len(set(int(seq[i]) for i in v)),
                                   repeated_identity_events=sum(repeats[i] for i in v)) for k, v in sorted(bins.items())],
                  metadata_word_indices=list(range(28 if nfft == 64 else 0, (28 if nfft == 64 else 0) + 3)),
                  limitations=['Arrival clock is router PCAP time, not RF TSF; absolute router clock is unsynchronized',
                               'BCM4366 frame-control header byte is a zero placeholder; QoS TID/retry/aggregation are not identified',
                               'Repeated identities are retained; complete events do not establish unique RF samples or map UDP slots',
                               'Pinned extractor overwrites three packed words with PHY status; no physical carrier mapping is applied',
                               'No AGC/phase calibration, 30-carrier mapping, resampling, receiver replication or PIWCSI1 output'])
    report_text = json.dumps(report, indent=2)
    output.mkdir(parents=True)
    np.savez_compressed(output / 'node-events.npz', packed_words=words, decoded_unscaled=decoded,
                        core_ids=np.asarray(cores, dtype='u1'), sequence_control=seq, chanspec=channels,
                        pcap_arrival_seconds=arrivals, event_start_seconds=starts,
                        repeated_identity_20ms=np.asarray(repeats, dtype=bool))
    (output / 'summary.json').write_text(report_text, encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pcap', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--nfft', type=int, choices=[64, 128, 256], default=64)
    parser.add_argument('--cores', type=int, nargs='+', default=[0, 1, 2])
    parser.add_argument('--source-mac', required=True)
    args = parser.parse_args()
    report = export(args.pcap, args.output, args.nfft, args.cores, args.source_mac)
    print(json.dumps({k: report[k] for k in ('model_ready', 'event_shape', 'csi_records',
                     'complete_contiguous_core_events', 'repeated_identity_events_20ms',
                     'arrival_interval_ms', 'twenty_event_first_to_last_ms')}))
