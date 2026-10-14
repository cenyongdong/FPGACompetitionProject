"""用人工可核算区间验证重叠、缺失、失配和SDK单位边界；不运行模型。"""
from pathlib import Path
from contextlib import contextmanager
import json
import hashlib
import uuid
import unittest

import analyze
import prepare


@contextmanager
def temporary_fixture():
    # Windows短名TEMP路径可能不在当前沙箱映射内；使用工作区新目录并保留夹具。
    root = prepare.ROOT / '.local/engine-timing-test-fixtures'
    root.mkdir(parents=True, exist_ok=True)
    folder = root / ('synthetic-' + uuid.uuid4().hex)
    folder.mkdir()
    yield str(folder)


def fixture():
    rows = [{'kind': 'runtime.forward', 'op_id': 0, 'slot': 0, 'frame_id': 10,
             'invocation': 0, 'begin_ns': 0, 'end_ns': 20_000_000}]
    ids = [0, 9185, 188, 9186, 192, 9187, 437, 9188, 442, 9189, 582, 9190, 649, 9191]
    for index, op in enumerate(ids):
        rows.append({**rows[0], 'kind': 'op.zg' if op >= 9185 else 'op.host', 'op_id': op,
                     'begin_ns': index * 1_000_000, 'end_ns': (index + 1) * 1_000_000})
    for kind, a, b in (('bridge.wait', 0, 400_000), ('bridge.allocate', 400_000, 450_000),
                       ('bridge.copy', 450_000, 500_000), ('bridge.cpu', 500_000, 800_000)):
        rows.append({**rows[0], 'kind': kind, 'op_id': 582, 'begin_ns': 10_000_000 + a,
                     'end_ns': 10_000_000 + b})
    frame = {'case': 'S11_01_308', 'invocation': 0, 'frame_id': 10, 'matched': True,
             'completed_layers': 745, 'host_callbacks': 7, 'zg_callbacks': 7}
    for field in ('process_ms', 'forward_ms', 'preprocess_ms', 'input_prepare_ms', 'state_clear_ms',
                  'final_wait_ms', 'output_read_ms', 'selection_ms', 'actual_save_ms', 'comparison_ms'):
        frame[field] = 20 if field == 'forward_ms' else 1
    summary = {'status': 'finite_numeric_run_completed', 'mode': 'wall', 'planned_frames': 1, 'completed_frames': 1}
    return rows, frame, summary


def write(run, rows, frame, summary):
    (run / 'monotonic-spans.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
    (run / 'frames.jsonl').write_text(json.dumps(frame) + '\n')
    (run / 'summary.json').write_text(json.dumps(summary))


class AnalysisTests(unittest.TestCase):
    def test_union_nested_and_overlapping(self):
        self.assertEqual(analyze.union_length([(0, 10), (2, 5), (8, 15), (20, 22)]), 17)
        self.assertEqual(analyze.union_length([]), 0)

    def test_forward_partition_not_double_counted(self):
        rows, _, _ = fixture()
        part = analyze.partition(rows)
        self.assertEqual(part['callback_union_ns'], 14_000_000)
        self.assertEqual(part['dispatch_callbacks_and_unobserved_ns'], 6_000_000)
        host = next(r for r in part['operators'] if r['op_id'] == 582)
        self.assertEqual(host['unattributed_ns'], 200_000)
        self.assertEqual(host['bridge_phases_ns']['bridge.wait'], 400_000)

    def test_overlapping_callbacks_rejected(self):
        rows, _, _ = fixture()
        rows[2]['begin_ns'] = 500_000
        with self.assertRaises(ValueError):
            analyze.partition(rows)

    def test_missing_and_wrong_callbacks_rejected(self):
        rows, _, _ = fixture()
        with self.assertRaises(ValueError):
            analyze.partition(rows[1:])
        rows[1]['op_id'] = 999
        with self.assertRaises(ValueError):
            analyze.partition(rows)

    def test_bridge_outside_parent_rejected(self):
        rows, _, _ = fixture()
        rows[-1]['end_ns'] = 11_100_000
        with self.assertRaises(ValueError):
            analyze.partition(rows)

    def test_inverted_and_cpu_negative_rejected(self):
        rows, _, _ = fixture()
        rows[0]['end_ns'] = -1
        with self.assertRaises(ValueError):
            analyze.validate_trace(rows)
        rows, _, _ = fixture()
        rows[0]['thread_cpu_ns'] = -10
        with self.assertRaises(ValueError):
            analyze.validate_trace(rows)

    def test_report_units_unknown_and_effective_copy_rate(self):
        with temporary_fixture() as folder:
            run = Path(folder)
            rows, frame, summary = fixture()
            write(run, rows, frame, summary)
            (run / 'transfers.jsonl').write_text(json.dumps({'kind': 'bridge.copy', 'direction': 'device_to_host',
                'op_id': 582, 'slot': 0, 'frame_id': 10, 'invocation': 0, 'logical_bytes': 100}) + '\n')
            report, _ = analyze.analyze(run)
            self.assertIsNone(report['unknown']['DDR_access_or_stall_ms'])
            self.assertIsNone(report['unknown']['NPU_pure_arithmetic_ms'])
            self.assertEqual(report['transfers'][0]['effective_api_MB_per_s'], 2)
            self.assertEqual(report['status'], 'finite_numeric_timing_evidence')

    def test_output_mismatch_and_frame_count_rejected(self):
        with temporary_fixture() as folder:
            run = Path(folder)
            rows, frame, summary = fixture()
            frame['matched'] = False
            write(run, rows, frame, summary)
            with self.assertRaises(ValueError):
                analyze.analyze(run)
            frame['matched'] = True
            summary['completed_frames'] = 2
            write(run, rows, frame, summary)
            with self.assertRaises(ValueError):
                analyze.analyze(run)

    def test_failed_wrapper_keeps_partial_not_success(self):
        with temporary_fixture() as folder:
            run = Path(folder)
            rows, frame, summary = fixture()
            write(run, rows, frame, summary)
            (run / 'exit.txt').write_text('124\n')
            report, _ = analyze.analyze(run)
            self.assertEqual(report['status'], 'partial_failed_evidence_only')
            self.assertEqual(report['forward_partitions'], [])

    def test_sdk_raw_unit_never_converted(self):
        with temporary_fixture() as folder:
            run = Path(folder)
            rows, frame, summary = fixture()
            summary['mode'] = 'sdk'
            write(run, rows, frame, summary)
            sdk = {'invocation': 0, 'op_id': 9185, 'wall_raw': 900000, 'copy_raw': 1,
                   'hardware_raw': 899999, 'other_raw': 0, 'unit': 'SDK_raw_unconfirmed'}
            (run / 'sdk-profile.jsonl').write_text(json.dumps(sdk) + '\n')
            hardware = {'invocation': 0, 'unit': 'ms', 'values': [0.01] * 745, 'collection_ms': 0.2}
            (run / 'hardware-layers.jsonl').write_text(json.dumps(hardware) + '\n')
            report, _ = analyze.analyze(run)
            self.assertEqual(report['SDK_raw'][0]['wall_raw'], 900000)
            self.assertAlmostEqual(report['hardware_samples'][0]['sum_of_layer_durations_ms_not_wall_partition'], 7.45)

    def test_patch_anchors_and_core_unchanged(self):
        engine = prepare.ROOT / 'software/core/inference/application_core.cpp'
        bridge = prepare.ROOT / 'software/core/inference/read_input_bridge.cpp'
        before = (prepare.sha(engine), prepare.sha(bridge))
        adapted = prepare.adapt_engine(engine.read_text(encoding='utf-8'))
        changed = prepare.adapt_bridge(bridge.read_text(encoding='utf-8'))
        self.assertIn('collect_timing_profile', adapted)
        self.assertIn('bridge.counter_wait', changed)
        with self.assertRaises(ValueError):
            prepare.adapt_engine(adapted)
        self.assertEqual(before, (prepare.sha(engine), prepare.sha(bridge)))

    def test_report_does_not_overwrite(self):
        with temporary_fixture() as folder:
            run = Path(folder)
            rows, frame, summary = fixture()
            write(run, rows, frame, summary)
            output = run / 'analysis'
            analyze.write_report(run, output)
            with self.assertRaises(FileExistsError):
                analyze.write_report(run, output)

    def test_tampered_evidence_rejected(self):
        with temporary_fixture() as folder:
            run = Path(folder)
            rows, frame, summary = fixture()
            write(run, rows, frame, summary)
            expected = hashlib.sha256((run / 'frames.jsonl').read_bytes()).hexdigest()
            (run / 'evidence-files.json').write_text(json.dumps({'frames.jsonl': expected}))
            report, _ = analyze.analyze(run)
            self.assertTrue(report['evidence_hashes_verified'])
            (run / 'frames.jsonl').write_text('{}\n')
            with self.assertRaises(ValueError):
                analyze.analyze(run)


if __name__ == '__main__':
    unittest.main()
