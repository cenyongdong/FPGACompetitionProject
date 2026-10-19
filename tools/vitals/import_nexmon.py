"""Read-only Nexmon PCAP adapter using an explicitly selected existing decoder.

Produces one row per actual complete three-core frame; does not resample or
claim that PCAP arrival timestamps are a verified sampling clock.
"""
import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np

from signal_fixtures import write_csv


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def convert(pcap, decoder_path, carriers, output):
    if len(carriers) != 4 or len(set(carriers)) != 4 or any(n < 0 or n >= 64 for n in carriers):
        raise ValueError("Require four distinct explicit 20MHz FFT indices in 0..63")
    spec = importlib.util.spec_from_file_location("existing_nexmon_decoder", decoder_path)
    decoder = importlib.util.module_from_spec(spec)
    old = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(decoder)
    finally:
        sys.dont_write_bytecode = old
    groups = {}
    identity = None
    for stamp, payload in decoder.pcap_udp(pcap):
        item = decoder.parse_payload(payload, 64)
        if item["chip"] != 106 or item["stream"] != 0 or item["core"] not in (0, 1, 2):
            raise ValueError("Require actual BCM4366 stream0 cores 0/1/2")
        if item["sequence_control"] & 15:
            raise ValueError("Fragmented source frames are outside this adapter")
        current = (item["mac"], item["chanspec"], item["stream"], item["chip"])
        if identity is None:
            identity = current
        if identity != current:
            raise ValueError("Mixed source/channel/stream identity")
        key = item["sequence_control"]
        group = groups.get(key)
        if group is None:
            if len(groups) >= 8192:
                raise ValueError("Frame budget exceeded")
            group = groups[key] = dict(time=stamp, cores={}, sequence=key >> 4)
        if item["core"] in group["cores"]:
            raise ValueError("Duplicate or wrapped frame identity; choose a smaller source capture")
        values = decoder.unpack_acphy(item["words"])
        if not all(math.isfinite(z.real) and math.isfinite(z.imag) for z in values):
            raise ValueError("Nonfinite decoded CSI")
        group["cores"][item["core"]] = values
        group["time"] = min(group["time"], stamp)
    frames = sorted(groups.values(), key=lambda g: g["time"])
    if not frames or any(set(g["cores"]) != {0, 1, 2} for g in frames):
        raise ValueError("Incomplete three-core frame; no chain replication or interpolation")
    pairs = np.empty((len(frames), 4, 2), dtype=np.complex128)
    combinations = ((0, 1), (0, 2), (1, 2), (0, 1))
    sequences = []
    extended = frames[0]["sequence"]
    previous = extended
    for row, frame in enumerate(frames):
        if row:
            delta = (frame["sequence"] - previous) % 4096
            if not 0 < delta < 2048:
                raise ValueError("Ambiguous radio sequence progression")
            extended += delta
            previous = frame["sequence"]
        sequences.append(extended)
        for ch, (a, b) in enumerate(combinations):
            pairs[row, ch] = frame["cores"][a][carriers[ch]], frame["cores"][b][carriers[ch]]
    relative = np.array([round((f["time"] - frames[0]["time"]) * 1e9) for f in frames], dtype=np.uint64)
    fixture = dict(pairs=pairs, times=relative, sequences=np.array(sequences, dtype=np.uint64),
                   valid=np.ones(len(frames), dtype=np.uint8), origin="real_capture",
                   clock="unknown_arrival", rate=50,
                   clock_evidence="relative PCAP arrival time; 50Hz is the target profile, not observed RF rate")
    write_csv(output, fixture)
    span = int(relative[-1]) / 1e9
    return dict(schema=1, source_pcap=str(pcap.resolve()), pcap_sha256=sha(pcap),
                decoder=str(decoder_path.resolve()), decoder_sha256=sha(decoder_path),
                complete_frames=len(frames), source_identity=identity,
                fft_indices=carriers, antenna_pairs=combinations,
                observed_arrival_rate_hz=(len(frames) - 1) / span if span else None,
                timestamp_basis="PCAP arrival time, reconstructed by existing float timestamp API",
                resampled=False, clock_verified=False, heart_ground_truth=False,
                output_csv=str(output.resolve()))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pcap", type=Path, required=True)
    p.add_argument("--decoder", type=Path, required=True)
    p.add_argument("--carriers", type=int, nargs=4, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists() or args.manifest.exists():
        raise ValueError("Preserve existing outputs; use fresh paths")
    manifest = convert(args.pcap, args.decoder, args.carriers, args.output)
    with args.manifest.open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
