"""Offline native-evidence replay and rejection checks; no device access."""
from pathlib import Path
import copy
import importlib.util
import json
import sys
from witness import compare


def read_run(path):
    path = Path(path)
    read = lambda name: json.loads((path/name).read_text())
    capture = read('observe-before/capture/result.json')
    before = capture['normalized']
    trace = read('cycletrace-before/raw.decoded.json')
    protocol = read('protocol-before/raw.decoded.json')
    raw = read('cycletrace-before/raw.json')
    release = capture['raw_snapshot']['release_words']
    assert before['first_RVALID_HP_cycle'] == (release[46] | release[47] << 32 if release[34] & 2 else None)
    for bank, decoded in zip(raw['banks'], trace['banks']):
        if bank['published']:
            for words, row in zip(bank['samples'], decoded['rows']):
                assert row['HP_cycle'] == words[0] | words[1] << 32
                assert row['PS_RVALID'] == (words[3] >> 30) & 1
    protocol['capture_HP_cycle'] = before['control']['capture_HP_cycle']
    protocol['live_status'] = before['control']['full_PC_status']
    protocol['valid'] = True
    return before, trace, protocol


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[3]
    gate_path = root/'FPGA/hdmi_candidate/diagnostics/deferred_consume_r45'
    sys.modules['consume_gate'] = load(gate_path/'gates/consume_gate.py', 'consume_gate')
    seed = load(gate_path/'before_seed_gate.py', 'seed')
    known, healthy, failed = [read_run(arg) for arg in sys.argv[1:4]]
    output = Path(sys.argv[4])
    actual = {}
    for name, sample, expected in (('known', known, True), ('healthy', healthy, True), ('r8', failed, False)):
        actual[name] = compare(*sample)
        assert actual[name]['consistent'] == expected
        gate = seed.evaluate(*sample)
        assert bool(gate['eligible'] or gate.get('continue_allowed')) == expected, gate
    assert actual['r8']['trace_minus_snapshot'] == 1
    assert actual['r8']['trace_cycle'] == actual['r8']['protocol_edge_cycle'] == 342540
    assert actual['r8']['snapshot_cycle'] == 342539 and not actual['r8']['signal_mismatches']
    cases = 3
    for offset in (-2, -1, 1, 2):
        before, trace, protocol = copy.deepcopy(known)
        before['first_RVALID_HP_cycle'] += offset
        assert not compare(before, trace, protocol)['consistent']
        assert not seed.evaluate(before, trace, protocol)['eligible']
        cases += 1
    for fault in ('boot', 'missing_protocol', 'missing_trace', 'row_gap', 'trigger', 'signal', 'no_preedge', 'protocol_origin'):
        before, trace, protocol = copy.deepcopy(known)
        if fault == 'boot': protocol['boot_id'] = 'other'
        if fault == 'missing_protocol': protocol['published'] = False
        if fault == 'missing_trace': trace['banks'][0]['published'] = False
        if fault == 'row_gap': trace['banks'][0]['rows'][8]['HP_cycle'] += 1
        if fault == 'trigger': trace['banks'][0]['trigger_cycle'] += 1
        if fault == 'signal': protocol['rows'][60]['PS_RDATA'] ^= 1
        if fault == 'no_preedge': protocol['rows'][0]['PS_RVALID'] = 1
        if fault == 'protocol_origin':
            for row in protocol['rows']: row['HP_cycle'] += 1
        assert not compare(before, trace, protocol)['consistent'], fault
        cases += 1
    if len(sys.argv) > 5:
        latest = read_run(sys.argv[5])
        actual['r9'] = compare(*latest)
        assert not actual['r9']['consistent']
        assert not seed.evaluate(*latest)['eligible']
        assert latest[0]['control']['full_PC_status'] & (1 << 79)
        # Counterfactual analysis only: a cosmetic timestamp edit must still
        # fail the original gate. Never write this value back to evidence.
        changed = copy.deepcopy(latest)
        changed[0]['first_RVALID_HP_cycle'] = changed[1]['banks'][0]['trigger_cycle']
        rejected = seed.evaluate(*changed)
        assert not rejected['eligible'] and not rejected['continue_allowed']
        assert rejected['reasons'] == ['Unknown native mandatory/capacity status']
        cases += 2
    result = dict(passed=True, cases=cases, actual=actual, old_seed_conditions_changed=False,
                  timestamp_adjustment=0, hardware_IO=0)
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(passed=True, cases=cases, actual=actual)))
