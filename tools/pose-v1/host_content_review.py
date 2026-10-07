"""Validate/inspect r4 Host content files offline; never runs a model or SDK."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

INPUT_SIZES = {(188, 0): 720, (192, 0): 30240, (192, 1): 16800, (437, 0): 400,
               (582, 0): 16800, (582, 1): 16800, (649, 0): 16800, (649, 1): 16800}
RESULT_SIZES = {(188, 0): 400, (188, 1): 400, (192, 0): 16800, (437, 0): 400,
                (437, 1): 400, (582, 0): 16800, (649, 0): 16800}


def need(yes, reason):
    if not yes:
        raise ValueError(reason)


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def read_records(output):
    folder = output / 'content'
    records = [json.loads(s) for s in (folder / 'index.jsonl').read_text(encoding='utf-8').splitlines() if s.strip()]
    raw, seen = {}, set()
    for row in records:
        need(row['case'] in ('S11_01_308', 'S11_01_309', 'S11_01_310',
                             'HOST_SMOKE_0', 'HOST_SMOKE_1', 'HOST_NEGATIVE'), 'Unknown/unsafe content case')
        need(row['kind'] in ('caller_input', 'input0_output', 'bridge_input', 'bridge_result', 'expected_mismatch'),
             'Unknown content capture kind')
        for key in ('invocation', 'frame_id', 'op_id', 'slot', 'bytes'):
            need(type(row[key]) is int and row[key] >= 0, 'Invalid content integer')
        name = f"call{row['invocation']}.{row['kind']}.op{row['op_id']}.slot{row['slot']}.f32"
        need(row['file'] == name and '/' not in name and '\\' not in name and name not in seen, 'Unsafe/duplicate content filename')
        seen.add(name)
        path = folder / name
        need(path.resolve().is_relative_to(folder.resolve()), 'Content path escapes directory')
        value = path.read_bytes()
        need(len(value) == row['bytes'] and 0 < len(value) <= 1024*1024 and len(value) % 4 == 0, 'Content bytes differ')
        meta = row['tensor']
        need(meta['allocated'] is True and meta['pointer'] == 'CPTR' and
             meta['region'] == 'icraft::xrt::HostMemRegionNode' and meta['bytes'] == len(value) and
             type(meta['offset']) is int and type(meta['chunk_bytes']) is int and
             0 <= meta['offset'] <= meta['chunk_bytes'] and len(value) <= meta['chunk_bytes'] - meta['offset'],
             'Content was not bounded Host CPTR')
        for flag in ('matches_expected', 'same_handle_as_caller', 'same_chunk_as_caller'):
            if flag in row:
                need(type(row[flag]) is bool, 'Invalid content boolean')
        raw[name] = value
    need({p.name for p in folder.iterdir() if p.is_file()} == seen | {'index.jsonl'}, 'Unlisted content file')
    return records, raw


def review_host(output):
    records, raw = read_records(output)
    need(len(records) == 5, 'Host content smoke incomplete')
    for invocation in (0, 1):
        expected = (np.arange(10800, dtype=np.float32) % np.float32(127)) / np.float32(16) - np.float32(4) + np.float32(invocation / 8)
        expected[0] = np.float32(-0.) if invocation == 0 else np.float32(0.)
        pair = [r for r in records if r['invocation'] == invocation]
        need(len(pair) == 2 and {r['kind'] for r in pair} == {'caller_input', 'input0_output'}, 'Host smoke pair differs')
        for row in pair:
            need(row['case'] == f'HOST_SMOKE_{invocation}' and row['frame_id'] == 100+invocation and
                 row['op_id'] == row['slot'] == 0 and row['matches_expected'] and
                 row['same_handle_as_caller'] and row['same_chunk_as_caller'] and
                 raw[row['file']] == expected.astype('<f4').tobytes(), 'Host SDK readback differs')
    negative = [r for r in records if r['invocation'] == 2]
    need(len(negative) == 1 and negative[0]['kind'] == 'expected_mismatch' and
         negative[0]['case'] == 'HOST_NEGATIVE' and negative[0]['frame_id'] == 102 and
         negative[0]['op_id'] == negative[0]['slot'] == 0 and negative[0]['matches_expected'] is False,
         'Expected mismatch was not rejected')
    positive = next(r for r in records if r['invocation'] == 1 and r['kind'] == 'caller_input')
    need(raw[negative[0]['file']] == raw[positive['file']], 'Mismatch test modified actual tensor')
    need(load(output / 'host-content-check.json') == dict(status='host_content_paths_passed', rounds=2,
         positive_records=4, expected_mismatch_rejected=True, unallocated_rejected=True, FP16_rejected=True,
         device_opened=False, session_created=False), 'Host content rejection summary differs')


def review_mixed(output, reference, calls):
    records, raw = read_records(output)
    need(len(records) == 17 * len(calls), 'Mixed content capture incomplete')
    for invocation, (name, frame) in enumerate(calls):
        selected = [r for r in records if r['invocation'] == invocation]
        keys = {(r['kind'], r['op_id'], r['slot']) for r in selected}
        wanted = {('caller_input', 0, 0), ('input0_output', 0, 0)}
        wanted |= {('bridge_input', op, slot) for op, slot in INPUT_SIZES}
        wanted |= {('bridge_result', op, slot) for op, slot in RESULT_SIZES}
        need(len(selected) == len(keys) == 17 and keys == wanted, 'Capture operator/slot coverage differs')
        expected = (reference / (name + '.input.f32')).read_bytes()
        for row in selected:
            need(row['case'] == name and row['frame_id'] == frame, 'Content frame differs')
            value = raw[row['file']]
            need(np.isfinite(np.frombuffer(value, dtype='<f4')).all(), 'Non-finite captured FP32')
            if row['kind'] in ('caller_input', 'input0_output'):
                need(row['matches_expected'] and value == expected, 'Actual caller/Input0 content differs')
                need('same_handle_as_caller' in row and 'same_chunk_as_caller' in row, 'Input alias evidence missing')
            else:
                sizes = INPUT_SIZES if row['kind'] == 'bridge_input' else RESULT_SIZES
                need(len(value) == sizes[row['op_id'], row['slot']], 'Bridge capture bytes differ')
    return records


def inspect_partial(output, reference):
    """Works with complete or early-stop content. Does not issue stage acceptance."""
    records, raw = read_records(output)
    report = {'status': 'content_diagnostic_inspected_not_stage_accepted', 'records': [], 'comparisons_to_first': [],
              'first_mismatch': None, 'numerical_accepted': False}
    first = {}
    for row in records:
        value = raw[row['file']]
        entry = dict(row, sha256=hashlib.sha256(value).hexdigest(),
                     all_finite=bool(np.isfinite(np.frombuffer(value, dtype='<f4')).all()))
        if row['kind'] in ('caller_input', 'input0_output') and not row['case'].startswith('HOST_'):
            expected = (reference / (row['case'] + '.input.f32')).read_bytes()
            equal = value == expected
            need(row.get('matches_expected') == equal, 'Capture mismatch flag contradicts actual bytes')
            entry['matches_fixed_reference'] = equal
            if not equal and report['first_mismatch'] is None:
                report['first_mismatch'] = dict(invocation=row['invocation'], frame_id=row['frame_id'], kind=row['kind'])
        key = row['kind'], row['op_id'], row['slot']
        if row['invocation'] == 0:
            first[key] = value
        elif key in first and len(first[key]) == len(value):
            x = np.frombuffer(first[key], dtype='<u4'); y = np.frombuffer(value, dtype='<u4')
            report['comparisons_to_first'].append(dict(invocation=row['invocation'], kind=row['kind'],
                  op_id=row['op_id'], slot=row['slot'], changed_elements=int(np.count_nonzero(x != y)),
                  bitwise_equal=value == first[key]))
        report['records'].append(entry)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, required=True)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    need(not args.output.exists(), 'Preserve prior diagnostic review')
    report = inspect_partial(args.results / 'results', args.reference)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print('Host content inspected; no stage or numerical acceptance generated.')
