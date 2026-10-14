"""解释Engine时间线：区间并集扣除嵌套；SDK/硬件时间另报，不臆造DDR占比。"""
from pathlib import Path
import argparse
import collections
import hashlib
import json
import math
import statistics

INIT = (1 << 64) - 1
PHASES = ('bridge.spec', 'bridge.wait', 'bridge.counter_wait', 'bridge.allocate',
          'bridge.copy', 'bridge.cpu', 'bridge.writeback')
LIMITS = (
    'bridge.wait为等待输入ready的宿主墙钟，不能全部归因NPU、DDR或SDK。',
    '硬件层计时包含算术、内部访存及可能的停顿，缺少独立DDR-stall计数。',
    'SDK四项tuple单位及跨forward累积语义未确认；保留raw，不与ms相减。',
    'SDK调用残余包含调度、回调观测和未覆盖工作，不能视为精确SDK调度时间。',
    '墙钟减线程CPU包括阻塞、抢占等；上下文切换计数不提供调度等待时长。',
    '逻辑搬运字节不是PL DDR总通信量，有效API吞吐不是DDR总线带宽。',
    '诊断采样、SDK profiling与输出落盘会扰动运行；baseline/wall/sdk须独立比较。',
    '本入口无VPU/TCP并发负载，结果不外推整机稳定性、5Hz或长期验收。',
)


def read_lines(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def union_length(intervals):
    """使用并集而非相加：允许嵌套/交叠，拒绝倒置区间。"""
    result, end = 0, None
    for begin, stop in sorted(intervals):
        if begin > stop:
            raise ValueError('Inverted interval')
        if end is None or begin >= end:
            result += stop - begin
            end = stop
        elif stop > end:
            result += stop - end
            end = stop
    return result


def stats(values):
    if not values:
        return None
    if not all(isinstance(x, (int, float)) and math.isfinite(x) for x in values):
        raise ValueError('Non-finite statistic')
    ordered = sorted(values)
    return {'samples': len(values), 'mean': statistics.mean(values), 'median': statistics.median(values),
            'p95_nearest_rank': ordered[math.ceil(len(values) * .95) - 1], 'max': ordered[-1]}


def one(rows, kind, required=True):
    found = [r for r in rows if r['kind'] == kind]
    if len(found) > 1 or (required and not found):
        raise ValueError('Missing/duplicate phase: ' + kind)
    return found[0] if found else None


def duration(row):
    return row['end_ns'] - row['begin_ns']


def inside(child, parent):
    return parent['begin_ns'] <= child['begin_ns'] <= child['end_ns'] <= parent['end_ns']


def validate_trace(rows):
    keys = set()
    for row in rows:
        for key in ('invocation', 'frame_id', 'op_id', 'slot', 'begin_ns', 'end_ns'):
            if type(row[key]) is not int:
                raise ValueError('Non-integer trace coordinate: ' + key)
        if row['begin_ns'] < 0 or duration(row) < 0:
            raise ValueError('Invalid wall interval')
        if not isinstance(row['kind'], str):
            raise ValueError('Invalid trace kind')
        key = (row['invocation'], row['kind'], row['op_id'], row['slot'], row['begin_ns'], row['end_ns'])
        if key in keys:
            raise ValueError('Duplicate trace record')
        keys.add(key)
        cpu = row.get('thread_cpu_ns')
        if cpu is not None and (type(cpu) is not int or cpu < 0):
            raise ValueError('Invalid thread CPU duration')
        for name in ('minor_faults', 'major_faults', 'voluntary_switches', 'involuntary_switches'):
            value = row.get(name)
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError('Invalid rusage delta: ' + name)


def partition(rows):
    forward = one(rows, 'runtime.forward')
    calls = [r for r in rows if r['kind'] in ('op.host', 'op.zg')]
    if len(calls) != 14 or len([r for r in calls if r['kind'] == 'op.zg']) != 7:
        raise ValueError('Expected7 Host and7 ZG callback spans')
    ids = [r['op_id'] for r in calls]
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate operator callback')
    if {r['op_id'] for r in calls if r['kind'] == 'op.host'} != {0, 188, 192, 437, 442, 582, 649} or \
       {r['op_id'] for r in calls if r['kind'] == 'op.zg'} != set(range(9185, 9192)):
        raise ValueError('Fixed callback identity differs')
    for call in calls:
        if not inside(call, forward):
            raise ValueError('Operator outside forward')
    call_union = union_length((r['begin_ns'], r['end_ns']) for r in calls)
    if call_union != sum(duration(r) for r in calls):
        raise ValueError('Overlapping callback spans; do not guess a sequential partition')
    bridge = [r for r in rows if r['kind'].startswith('bridge.')]
    by_operator = []
    for call in sorted(calls, key=lambda r: r['begin_ns']):
        children = [r for r in bridge if r['op_id'] == call['op_id']]
        if any(not inside(r, call) for r in children):
            raise ValueError('Bridge span outside corresponding operator callback')
        measured = union_length((r['begin_ns'], r['end_ns']) for r in children)
        cpu = call.get('thread_cpu_ns')
        by_operator.append({'op_id': call['op_id'], 'backend': call['kind'], 'inclusive_ns': duration(call),
                            'thread_cpu_ns': cpu,
                            'wall_minus_thread_cpu_ns': duration(call) - cpu if cpu is not None else None,
                            'observed_bridge_union_ns': measured,
                            'unattributed_ns': duration(call) - measured,
                            'bridge_phases_ns': {kind: sum(duration(r) for r in children if r['kind'] == kind)
                                                 for kind in PHASES}})
    if any(r['op_id'] not in ids for r in bridge):
        raise ValueError('Bridge without operator callback')
    return {'forward_ns': duration(forward), 'callback_union_ns': call_union,
            'dispatch_callbacks_and_unobserved_ns': duration(forward) - call_union,
            'operators': by_operator}


def analyze(run):
    hashes_path = run / 'evidence-files.json'
    if (run / 'run-identity.json').exists() and not hashes_path.exists():
        raise ValueError('Audited run missing complete evidence hash list')
    if hashes_path.exists():
        hashes = json.loads(hashes_path.read_text(encoding='utf-8'))
        if not isinstance(hashes, dict) or not hashes:
            raise ValueError('Empty evidence hash list')
        root = run.resolve()
        for name, expected in hashes.items():
            relative = Path(name)
            path = (run / relative).resolve()
            if relative.is_absolute() or '..' in relative.parts or root not in path.parents:
                raise ValueError('Evidence path escapes run')
            digest = hashlib.sha256()
            with path.open('rb') as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    digest.update(block)
            if digest.hexdigest() != expected:
                raise ValueError('Evidence identity changed: ' + name)
    result_dir = run / 'results' if (run / 'results').exists() else run
    summary_path = result_dir / 'summary.json'
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}
    frames = read_lines(result_dir / 'frames.jsonl')
    rows = read_lines(result_dir / 'monotonic-spans.jsonl')
    validate_trace(rows)
    hardware = read_lines(result_dir / 'hardware-layers.jsonl')
    sdk = read_lines(result_dir / 'sdk-profile.jsonl')
    complete = summary.get('status') == 'finite_numeric_run_completed'
    if summary and summary.get('mode') not in ('baseline', 'wall', 'sdk'):
        raise ValueError('Unknown completed-run mode')
    if (run / 'exit.txt').exists() and (run / 'exit.txt').read_text().strip() != '0':
        complete = False
    if complete:
        if summary.get('planned_frames') != summary.get('completed_frames') or len(frames) != summary['planned_frames']:
            raise ValueError('Summary/frame count differs')
        if [r['invocation'] for r in frames] != list(range(len(frames))) or not all(r['matched'] for r in frames):
            raise ValueError('Non-contiguous or mismatched completed frames')
        if any(r['completed_layers'] != 745 or r['host_callbacks'] != 7 or r['zg_callbacks'] != 7 for r in frames):
            raise ValueError('Runtime callback/count contract differs')
    by_frame = collections.defaultdict(list)
    for r in rows:
        by_frame[r['invocation']].append(r)
    partitions = []
    if complete and summary.get('mode') != 'baseline':
        if set(by_frame) - {INIT} != set(range(len(frames))) or any(r.get('failed') for r in rows):
            raise ValueError('Trace coverage/exception differs')
        for f in frames:
            partitions.append({'invocation': f['invocation'], **partition(by_frame[f['invocation']])})
    transfer_rows = read_lines(result_dir / 'transfers.jsonl')
    transfers = []
    for transfer in transfer_rows:
        matches = [r for r in by_frame[transfer['invocation']] if r['kind'] == transfer['kind']
                   and r['op_id'] == transfer['op_id'] and r['slot'] == transfer['slot']]
        if len(matches) != 1 or type(transfer['logical_bytes']) is not int or transfer['logical_bytes'] <= 0:
            raise ValueError('Invalid transfer metadata/span association')
        ns = duration(matches[0])
        transfers.append({**transfer, 'api_elapsed_ns': ns,
                          'effective_api_MB_per_s': transfer['logical_bytes'] * 1000 / ns if ns > 0 else None})
    measured = collections.defaultdict(list)
    cpu = collections.defaultdict(list)
    usage = collections.defaultdict(lambda: collections.defaultdict(list))
    for row in rows:
        if row['invocation'] == INIT:
            continue
        label = row['kind'] + (':' + str(row['op_id']) if row['kind'].startswith(('bridge.', 'op.')) else '')
        measured[label].append(duration(row) / 1e6)
        if row.get('thread_cpu_ns') is not None:
            cpu[label].append(row['thread_cpu_ns'] / 1e6)
        for key in ('minor_faults', 'major_faults', 'voluntary_switches', 'involuntary_switches'):
            if row.get(key) is not None:
                usage[label][key].append(row[key])
    layer_summary = []
    for row in hardware:
        values = row['values']
        if row.get('unit') != 'ms' or len(values) != 745 or not all(isinstance(x, (int, float)) and math.isfinite(x) and x >= 0 for x in values):
            raise ValueError('Invalid hardware layer sample')
        layer_summary.append({'invocation': row['invocation'], 'layer_ms': stats(values),
                              'sum_of_layer_durations_ms_not_wall_partition': sum(values),
                              'all_zero_unusable': not any(values),
                              'collection_ms_outside_engine': row['collection_ms']})
    if complete and summary.get('mode') == 'sdk':
        if [r['invocation'] for r in hardware] != list(range(len(frames))) or not sdk:
            raise ValueError('Missing SDK/hardware profile sample')
    for row in sdk:
        if row.get('unit') != 'SDK_raw_unconfirmed' or not all(isinstance(row[key], (int, float)) and math.isfinite(row[key])
                                                             for key in ('wall_raw', 'copy_raw', 'hardware_raw', 'other_raw')):
            raise ValueError('Invalid SDK raw profile')
    report = {
        'status': 'finite_numeric_timing_evidence' if complete else 'partial_failed_evidence_only',
        'summary': summary, 'frame_metric_ms': {key: stats([f[key] for f in frames]) for key in
             ('process_ms', 'forward_ms', 'preprocess_ms', 'input_prepare_ms', 'state_clear_ms', 'final_wait_ms',
              'output_read_ms', 'selection_ms', 'actual_save_ms', 'comparison_ms') if frames},
        'wall_ms': {key: stats(value) for key, value in sorted(measured.items())},
        'thread_cpu_ms': {key: stats(value) for key, value in sorted(cpu.items())},
        'thread_events': {key: {k: stats(v) for k, v in values.items()} for key, values in usage.items()},
        'initialization_spans': by_frame.get(INIT, []), 'forward_partitions': partitions,
        'transfers': transfers, 'hardware_samples': layer_summary, 'SDK_raw': sdk,
        'unknown': {'NPU_pure_arithmetic_ms': None, 'DDR_access_or_stall_ms': None,
                    'exact_SDK_dispatch_ms': None, 'OS_runqueue_delay_ms': None},
        'limitations': list(LIMITS),
    }
    report['evidence_hashes_verified'] = hashes_path.exists()
    return report, rows


def compare(report, baseline_run):
    baseline, _ = analyze(baseline_run)
    if baseline['status'] != 'finite_numeric_timing_evidence' or baseline['summary'].get('mode') != 'baseline':
        raise ValueError('A successful baseline run is required')
    if report['status'] != 'finite_numeric_timing_evidence':
        raise ValueError('Cannot compare a failed run as successful timing')
    # 运行包装器的审查身份必须相同；profile模式是唯一预期差异。
    current_identity = report.get('run_identity')
    baseline_path = baseline_run / 'run-identity.json'
    if not current_identity or not baseline_path.exists():
        raise ValueError('Identity-audited board wrappers required for comparison')
    previous = json.loads(baseline_path.read_text())
    for key in ('package_sha256', 'binary_sha256', 'cycles', 'board_preflight_identity'):
        if current_identity.get(key) != previous.get(key):
            raise ValueError('Comparison condition changed: ' + key)
    output = {}
    for key in ('process_ms', 'forward_ms'):
        a = baseline['frame_metric_ms'][key]['mean']
        b = report['frame_metric_ms'][key]['mean']
        output[key] = {'baseline_mean_ms': a, 'instrumented_mean_ms': b,
                       'difference_ms': b - a, 'ratio': b / a if a else None}
    output['interpretation'] = 'Sequential run comparison; includes run variation, not an exact correction factor.'
    return output


def markdown(report):
    lines = ['# Engine计时分析', '', '状态：' + report['status'], '',
             '| Engine阶段 | 均值/ms | P95/ms | 最大/ms |', '|---|---:|---:|---:|']
    for name, row in report['frame_metric_ms'].items():
        lines.append(f"| {name} | {row['mean']:.6f} | {row['p95_nearest_rank']:.6f} | {row['max']:.6f} |")
    lines += ['', '下面是含子区间的观测跨度，不能与上表直接相加。', '',
              '| 观测跨度 | 墙钟均值/ms | 线程CPU均值/ms |', '|---|---:|---:|']
    for name, row in report['wall_ms'].items():
        cpu = report['thread_cpu_ms'].get(name)
        lines.append(f"| {name} | {row['mean']:.6f} | " + (f"{cpu['mean']:.6f}" if cpu else '未知') + ' |')
    lines += ['', 'forward_partitions中的残余为调度、回调与未覆盖工作的混合量。',
              '硬件层计时及SDK原始字段是独立证据，不参与墙钟饼图或直接扣减。', '', '## 测量限制', '']
    lines += ['- ' + item for item in report['limitations']]
    if 'baseline_comparison' in report:
        lines += ['', '## 同身份基线比较', '', '```json', json.dumps(report['baseline_comparison'], indent=2), '```']
    return '\n'.join(lines) + '\n'


def write_report(run, output, baseline=None):
    report, rows = analyze(run)
    identity = run / 'run-identity.json'
    if identity.exists():
        report['run_identity'] = json.loads(identity.read_text())
    if baseline:
        report['baseline_comparison'] = compare(report, baseline)
    if output.exists():
        raise FileExistsError('Preserve prior analysis')
    output.mkdir(parents=True)
    (output / 'report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
    (output / 'report.md').write_text(markdown(report), encoding='utf-8')
    trace = []
    for row in rows:
        lane = 'initialization' if row['invocation'] == INIT else row['kind'].split('.')[0]
        trace.append({'name': row['kind'] + ':' + str(row['op_id']), 'cat': lane, 'ph': 'X',
                      'pid': 1 if row['invocation'] == INIT else row['invocation'] + 2, 'tid': lane,
                      'ts': row['begin_ns'] / 1000, 'dur': duration(row) / 1000, 'args': row})
    (output / 'chrome-trace.json').write_text(json.dumps({'traceEvents': trace}, allow_nan=False) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--baseline', type=Path)
    args = parser.parse_args()
    result = write_report(args.run, args.output, args.baseline)
    print(result['status'], args.output / 'report.md')
