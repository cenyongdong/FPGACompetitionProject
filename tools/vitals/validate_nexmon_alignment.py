"""Known-signal tests on recorded RX times plus unchanged C++ synthetic-only checks."""
import argparse
import json
from pathlib import Path
import subprocess

import numpy as np

from align_nexmon_phase import align_phase
from audit_nexmon_vitals import save
from signal_fixtures import write_csv
from test_align_nexmon_phase import analytic, clock
from validate_timing_adapter import synthetic_fixture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--aligned-root', type=Path, required=True)
    parser.add_argument('--executable', type=Path, required=True)
    args = parser.parse_args()
    root = args.aligned_root.resolve()
    output = root / 'validation'
    output.mkdir(exist_ok=False)
    checks = []
    # Actual recorded TIMESTAMPS only; values are wholly synthetic and NOT evidence
    # of a human heartbeat in the associated recording. No capture is lengthened.
    for name in ('latest-phone', 'earlier-ap', 'stable-round2'):
        with np.load(root / name / 'phase-arrays.npz') as z:
            t = z['source_ns']
        for hz in (.8, 1.2, 2.0):
            def values(stamps):
                seconds = stamps / 1e9
                return np.column_stack([.3 * np.sin(2 * np.pi * .25 * seconds + ch * .1) +
                                        .03 * np.sin(2 * np.pi * hz * seconds + ch * .2)
                                        for ch in range(4)])
            arrays, quality = align_phase(t, values(t))
            truth = values(arrays['grid_ns'])
            good = arrays['valid']
            if not good.any():
                raise ValueError('No supported output samples for a known-signal timing test')
            error = float(np.sqrt(np.mean((arrays['phase'][good] - truth[good]) ** 2)))
            row = dict(case=name, origin='synthetic_values_on_recorded_RX_times',
                frequency_hz=hz, known_bpm=hz * 60,
                phase_rmse_rad=error, valid_feature_samples=int(good.sum()),
                invalid_feature_samples=int((~good).sum()),
                phase_faults=quality['source_phase_jumps'],
                source_gap_faults=quality['source_gap_faults'],
                output_interval_ms=20, clock_or_duration_not_extended=True,
                passed=bool(error < 1e-4 and not any(quality['source_phase_jumps'])))
            checks.append(row)
    # Isolate the aliasing behavior on uniform known input: 48.8Hz aliases to 1.2Hz
    # under naive 300/6 selection. Keep its phase steps below the original gate.
    t = clock(10)
    alias = np.tile((.1 * np.sin(2 * np.pi * 48.8 * t / 1e9))[:, None], (1, 4))
    arrays, _ = align_phase(t, alias)
    before = float(np.sqrt(np.mean(alias[::6] ** 2)))
    after = float(np.sqrt(np.mean(arrays['phase'] ** 2)))
    checks.append(dict(case='known_48_8hz_alias', origin='synthetic',
        naive_decimation_rms_rad=before, filtered_rms_rad=after,
        measured_attenuation_db=float(20 * np.log10(before / max(after, 1e-300))),
        passed=bool(after < before / 1000)))
    # Independent 44s synthetic histories, not extended/repeated real recordings.
    # Encode as complex antenna pairs only here, with explicit synthetic provenance.
    t = clock()
    for name, phase, expected_heart in (
            ('analytic72', analytic(t), True),
            ('breath_only', np.column_stack([.3 * np.sin(2 * np.pi * .25 * t / 1e9 + ch * .1)
                                            for ch in range(4)]), False)):
        arrays, quality = align_phase(t, phase)
        if not arrays['valid'].all() or not quality['windows']['locally_qualified_windows']:
            raise ValueError('Synthetic history unexpectedly failed local timing/phase gate')
        fixture = synthetic_fixture(arrays['grid_ns'], arrays['phase'], 50)
        csv, native = output / f'{name}.csv', output / f'{name}-native.json'
        write_csv(csv, fixture)
        command = [str(args.executable.resolve()), '--input', str(csv), '--output', str(native)]
        process = subprocess.run(command, capture_output=True, text=True, timeout=30)
        save(output / f'{name}-process.json', dict(command=command, exit_code=process.returncode,
                                                stdout=process.stdout, stderr=process.stderr))
        if process.returncode:
            raise RuntimeError('Native synthetic check failed; original process output retained')
        result = json.loads(native.read_text(encoding='utf-8'))
        heart = result['heart']
        passed = (heart is not None and abs(heart['bpm'] - 72) <= 1.0) if expected_heart else heart is None
        checks.append(dict(case=name, origin='wholly_synthetic_44s',
            status=result['status'], reasons=result['reasons'], heart=heart,
            passed=bool(passed)))
    result = dict(scope='host_offline_signal_adaptation_tests', checks=checks,
        all_passed=all(row['passed'] for row in checks),
        real_heart_rate_detection_or_accuracy_validated=False,
        source_phase_jumps_repaired=False, hardware_accessed=False,
        strict_cpp_algorithm_changed=False)
    save(output / 'checks.json', result)
    print(json.dumps(result, indent=2))
    if not result['all_passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
