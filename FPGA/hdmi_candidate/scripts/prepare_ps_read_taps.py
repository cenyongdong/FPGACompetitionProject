"""Generate an isolated PS read-only tap variant; never edits its source tree.

The generated top reuses the original generated child modules. This performs
source-identity, exact inverse-transformation and text/width checks only. It
does not run an HDL compiler, EDA, SDK, a device connection or board workload.
"""
from pathlib import Path
import argparse
import difflib
import hashlib
import json
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
PS_REL = 'fpai_demo_vivado.srcs/sources_1/bd/ps_ai/synth/ps_ai.v'
WRAPPER_REL = 'rtl/ps_ai_wrapper.sv'
IDENTITY = ROOT / 'tools/pose-v1/evidence/hdmi-live-20261017-r2/static-read-path/source-identity.json'
EXPECTED = {
    PS_REL: 'b253cc32badb6bc182e3dfce3e5732b43229d6d93ca07e2d98b582783700a5e2',
    WRAPPER_REL: 'fb4a10daf8891317ff9f34943b1723febaa383232bfd74b11f542277ad71063c',
}
PORTS = ('diagnostic_hp2_read', 'diagnostic_hp2_clk', 'diagnostic_hp2_resetn')
# name, most-significant bit, least-significant bit; exact requested ABI.
FIELDS = [
    ('ARADDR', 31, 0), ('ARID', 37, 32), ('ARLEN', 41, 38),
    ('ARSIZE', 44, 42), ('ARBURST', 46, 45), ('ARLOCK', 48, 47),
    ('ARCACHE', 52, 49), ('ARPROT', 55, 53), ('ARQOS', 59, 56),
    ('ARVALID', 60, 60), ('ARREADY', 61, 61),
    ('RVALID', 62, 62), ('RREADY', 63, 63), ('RID', 69, 64),
    ('RRESP', 71, 70), ('RLAST', 72, 72),
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def mask_comments_and_strings(source):
    """Keep offsets/newlines while hiding keyword-like comment/string content."""
    pattern = r'//[^\r\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"'
    return re.sub(pattern, lambda m: ''.join(c if c in '\r\n' else ' ' for c in m[0]), source)


def module_span(source, name):
    masked = mask_comments_and_strings(source)
    tokens = list(re.finditer(r'\bmodule\s+(\w+)\b|\bendmodule\b', masked))
    modules, current = [], None
    for token in tokens:
        if token[1] is not None:
            require(current is None, 'nested/incomplete module declaration')
            current = token
        else:
            require(current is not None, 'endmodule without module')
            modules.append((current[1], current.start(), token.end(), current))
            current = None
    require(current is None, 'incomplete final module')
    chosen = [x for x in modules if x[0] == name]
    require(len(chosen) == 1, f'unique complete module required: {name}')
    _, start, end, token = chosen[0]
    line_start = source.rfind('\n', 0, start) + 1
    require(not source[line_start:start].strip(), 'module must start on its own line')
    # Preserve whole immediately preceding attribute lines, including the
    # original CORE_GENERATION_INFO/HW_HANDOFF. Do not copy another module.
    start = line_start
    while start:
        previous_end = start - 1
        previous_start = source.rfind('\n', 0, previous_end) + 1
        previous = source[previous_start:previous_end].rstrip('\r')
        if not re.fullmatch(r'\s*(?:\(\*.*?\*\)\s*)+', previous):
            break
        start = previous_start
    if source[end:end + 2] == '\r\n':
        end += 2
    elif source[end:end + 1] == '\n':
        end += 1
    return start, end, token.start(1), token.end(1)


def closing_parenthesis(masked, opening):
    require(masked[opening] == '(', 'expected opening parenthesis')
    depth = 0
    for pos in range(opening, len(masked)):
        depth += (masked[pos] == '(') - (masked[pos] == ')')
        if not depth:
            return pos
    raise ValueError('unclosed parenthesis')


def header_end(source, module_name):
    masked = mask_comments_and_strings(source)
    hits = list(re.finditer(r'\bmodule\s+' + re.escape(module_name) + r'\s*\(', masked))
    require(len(hits) == 1, f'unsupported/ambiguous header: {module_name}')
    close = closing_parenthesis(masked, hits[0].end() - 1)
    semicolon = re.match(r'\s*;', masked[close + 1:])
    require(semicolon is not None, 'module header semicolon missing')
    return close, close + 1 + semicolon.end()


def transform(source, edits):
    """Apply non-overlapping edits and prove exact byte reversal."""
    edits.sort(key=lambda x: (x['start'], x['end']))
    previous_end = -1
    for item in edits:
        require(item['start'] >= previous_end, 'overlapping edits')
        require(source[item['start']:item['end']] == item['old'], 'edit source mismatch')
        previous_end = item['end']
    result = source
    for item in reversed(edits):
        result = result[:item['start']] + item['new'] + result[item['end']:]
    delta = 0
    for item in edits:
        item['output_start'] = item['start'] + delta
        item['output_end'] = item['output_start'] + len(item['new'])
        delta += len(item['new']) - len(item['old'])
    restored = result
    for item in reversed(edits):
        a, b = item['output_start'], item['output_end']
        require(restored[a:b] == item['new'], 'inverse expected bytes mismatch')
        restored = restored[:a] + item['old'] + restored[b:]
    require(restored.encode('ascii') == source.encode('ascii'), 'inverse byte identity failed')
    return result, {'passed': True, 'restored_SHA256': sha(restored.encode('ascii')),
                    'original_SHA256': sha(source.encode('ascii')), 'edits': edits}


def add_edit(edits, start, end, old, new, reason):
    edits.append({'start': start, 'end': end, 'old': old, 'new': new, 'reason': reason})


def newline(source):
    return '\r\n' if '\r\n' in source else '\n'


def make_top(full_source):
    require(not any(name in full_source for name in PORTS), 'diagnostic names already exist')
    start, end, name_start, name_end = module_span(full_source, 'ps_ai')
    original = full_source[start:end]
    nl = newline(original)
    close, declaration_start = header_end(original, 'ps_ai')
    require(not re.search(r'\b(input|output|inout)\b',
                          mask_comments_and_strings(original[:close])), 'expected non-ANSI PS header')
    masked = mask_comments_and_strings(original)
    ends = list(re.finditer(r'\bendmodule\b', masked))
    require(len(ends) == 1, 'PS extraction includes another module')
    assignments = []
    declarations = []
    for field, hi, lo in FIELDS:
        signal = 'axi_interconnect_4_M00_AXI_' + field
        expected_width = hi - lo + 1
        matches = list(re.finditer(r'\bwire\s*(?:\[\s*(\d+)\s*:\s*(\d+)\s*\])?\s*'
                                   + re.escape(signal) + r'\s*;', original))
        require(len(matches) == 1, f'unique tap wire required: {signal}')
        match = matches[0]
        width = abs(int(match[1]) - int(match[2])) + 1 if match[1] else 1
        require(width == expected_width, f'tap width mismatch: {signal}: {width}/{expected_width}')
        declarations.append({'signal': signal, 'width': width,
                             'source_line': full_source.count('\n', 0, start + match.start()) + 1,
                             'raw_declaration': match[0], 'tap_hi': hi, 'tap_lo': lo})
        slice_text = f'[{hi}:{lo}]' if hi != lo else f'[{lo}]'
        assignments.append(f'  assign diagnostic_hp2_read{slice_text} = {signal};')
    for signal in ['hp_axi_aclk_1', 'proc_sys_reset_1_peripheral_aresetn']:
        hits = list(re.finditer(r'\bwire\s*(?:\[\s*(\d+)\s*:\s*(\d+)\s*\])?\s*'
                               + re.escape(signal) + r'\s*;', original))
        require(len(hits) == 1, f'unique clock/reset source required: {signal}')
        match = hits[0]
        width = abs(int(match[1]) - int(match[2])) + 1 if match[1] else 1
        require(width == 1, f'clock/reset source must have one bit: {signal}')
        declarations.append({'signal': signal, 'width': width,
                             'source_line': full_source.count('\n', 0, start + match.start()) + 1,
                             'raw_declaration': match[0]})
    assignments += ["  assign diagnostic_hp2_read[127:73] = 55'd0;",
                    '  assign diagnostic_hp2_clk = hp_axi_aclk_1;',
                    '  assign diagnostic_hp2_resetn = proc_sys_reset_1_peripheral_aresetn;']
    edits = []
    add_edit(edits, name_start - start, name_end - start, 'ps_ai', 'ps_ai_read_observed', 'module identifier only')
    add_edit(edits, close, close, '', ',' + nl + '    ' + (',' + nl + '    ').join(PORTS), 'append non-ANSI output port names')
    ports = nl + '  output [127:0] diagnostic_hp2_read;' + nl
    ports += '  output diagnostic_hp2_clk;' + nl + '  output diagnostic_hp2_resetn;' + nl
    add_edit(edits, declaration_start, declaration_start, '', ports, 'declare three new outputs')
    body = nl + nl.join(assignments) + nl
    add_edit(edits, ends[0].start(), ends[0].start(), '', body, 'append only continuous tap assignments')
    observed, proof = transform(original, edits)
    require(len(re.findall(r'\bmodule\s+', mask_comments_and_strings(observed))) == 1, 'child module accidentally copied')
    timescale = re.findall(r'^\s*`timescale[^\r\n]*(?:\r?\n|$)', full_source, re.MULTILINE)
    require(len(timescale) == 1, 'expected one original timescale directive')
    preamble = timescale[0].lstrip('\r\n')
    proof.update({'source_span_start': start, 'source_span_end_exclusive': end,
                  'source_line_start': full_source.count('\n', 0, start) + 1,
                  'source_line_end': full_source.count('\n', 0, end - 1) + 1,
                  'copied_timescale': preamble, 'submodules_copied': 0,
                  'original_ports_assignments_and_connections_byte_identical_after_inverse': True})
    return preamble + observed, proof, declarations, original


def make_wrapper(source):
    require(not any(name in source for name in PORTS), 'wrapper diagnostic names already exist')
    start, end, _, _ = module_span(source, 'ps_ai_wrapper')
    require(not source[:start].strip().endswith('endmodule'), 'unexpected wrapper prefix module')
    close, _ = header_end(source, 'ps_ai_wrapper')
    require(re.search(r'\b(input|output|inout)\b', mask_comments_and_strings(source[:close])), 'expected ANSI wrapper header')
    masked = mask_comments_and_strings(source)
    instances = list(re.finditer(r'\bps_ai\s+ps_ai_i\s*\(', masked))
    require(len(instances) == 1, 'expected exactly ps_ai ps_ai_i instance')
    instance = instances[0]
    instance_close = closing_parenthesis(masked, instance.end() - 1)
    require(instance_close < end, 'instance outside wrapper module')
    nl = newline(source)
    edits = []
    ports = ',' + nl + '    output [127:0] diagnostic_hp2_read,' + nl
    ports += '    output diagnostic_hp2_clk,' + nl + '    output diagnostic_hp2_resetn' + nl
    add_edit(edits, close, close, '', ports, 'append ANSI output ports')
    add_edit(edits, instance.start(), instance.start() + len('ps_ai'), 'ps_ai',
             'ps_ai_read_observed', 'change only ps_ai_i module type')
    connections = ',' + nl + (',' + nl).join(f'  .{port}({port})' for port in PORTS) + nl
    add_edit(edits, instance_close, instance_close, '', connections, 'connect only new explicit ports')
    observed, proof = transform(source, edits)
    proof['original_ports_assignments_and_connections_byte_identical_after_inverse'] = True
    return observed, proof


def self_test():
    # Exercise comment/string keyword masking, adjacent modules, module
    # attributes, extraction, header/instance insertion and exact reversal.
    nl = '\n'
    declarations = []
    for field, hi, lo in FIELDS:
        width = hi - lo + 1
        vector = f'[{width - 1}:0] ' if width > 1 else ''
        declarations.append(f'wire {vector}axi_interconnect_4_M00_AXI_{field};')
    source = '`timescale 1 ps / 1 ps\nmodule helper(); endmodule\n'
    source += '(* NOTE = "module fake; endmodule" *)\nmodule ps_ai(input_name);\ninput input_name;\n'
    source += '// module ps_ai; endmodule\n/* module ps_ai; endmodule */\n'
    source += nl.join(declarations) + '\nwire hp_axi_aclk_1;\nwire [0:0] proc_sys_reset_1_peripheral_aresetn;\n'
    source += 'endmodule\nmodule tail(); endmodule\n'
    output, proof, wires, extracted = make_top(source)
    require(proof['passed'] and len(wires) == 18 and 'module helper' not in output
            and 'module tail' not in output and '(* NOTE' in output, 'synthetic extraction failed')
    wrapper = 'module ps_ai_wrapper(input input_name);\nps_ai ps_ai_i(.input_name(input_name));\nendmodule\n'
    _, wrapper_proof = make_wrapper(wrapper)
    require(wrapper_proof['passed'], 'synthetic wrapper inverse failed')
    negative = []
    for name, bad in [('duplicate module', source + '\nmodule ps_ai(); endmodule\n'),
                      ('missing endmodule', 'module ps_ai();\n'),
                      ('wrong RID width', source.replace('wire [5:0] axi_interconnect_4_M00_AXI_RID;',
                                                          'wire [4:0] axi_interconnect_4_M00_AXI_RID;'))]:
        try:
            make_top(bad)
        except ValueError:
            negative.append(name)
        else:
            raise ValueError(f'negative synthetic check did not reject: {name}')
    positions = [bit for _, hi, lo in FIELDS for bit in range(lo, hi + 1)]
    require(positions == list(range(73)), 'tap layout must be contiguous bits0..72')
    require(128 - len(positions) == 55, 'reserved field width must be55')
    walking_one = []
    for field, hi, lo in FIELDS:
        for bit in range(hi - lo + 1):
            value = 1 << bit
            packed = value << lo
            require(packed < 1 << 73 and (packed >> lo) == value, 'packing layout check failed')
            walking_one.append({'field': field, 'field_bit': bit, 'tap_bit': lo + bit})
    return {'passed': True, 'checks': ['comment/string masking', 'adjacent module exclusion',
            'original module attributes preserved', 'PS exact inverse', 'wrapper exact inverse',
            '18 wire widths', '73 active plus55 zero bits', '73 walking-one layout checks'],
            'negative_cases_rejected': negative, 'walking_one': walking_one,
            'scope': 'pure Python text/bit-layout checks; no HDL compilation'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-reference', required=True, type=Path)
    parser.add_argument('--output-directory', required=True, type=Path)
    args = parser.parse_args()
    reference, out = args.source_reference.resolve(), args.output_directory.resolve()
    require(not out.exists(), f'refusing to overwrite existing output: {out}')
    require(out != reference and out not in reference.parents, 'output cannot replace/contain source reference')
    require(reference not in out.parents, 'output must be outside protected source reference')
    out.mkdir(parents=True)
    started = time.monotonic()
    report = {'passed': False, 'working_directory': str(Path.cwd()),
              'source_reference': str(reference), 'output_directory': str(out),
              'arguments': sys.argv[1:], 'board_or_SDK_access': False, 'EDA_or_HDL_compilation': False,
              'sources': {}, 'outputs': {}, 'pass_criteria': 'r2 source SHA +18 exact wire widths + exact inverses + synthetic checks',
              'stop_condition': 'source/format/width/inverse mismatch; no generated output accepted on failure',
              'limits': {'max_source_bytes_per_file': 2 * 1024 * 1024}}
    try:
        identity_bytes = IDENTITY.read_bytes()
        identity = {entry['path']: entry for entry in json.loads(identity_bytes)}
        (out / 'r2-source-identity.json').write_bytes(identity_bytes)
        report['r2_source_identity_SHA256'] = sha(identity_bytes)
        contents = {}
        for rel, expected in EXPECTED.items():
            path = reference / rel
            require(path.stat().st_size <= report['limits']['max_source_bytes_per_file'], 'source exceeds size bound')
            raw = path.read_bytes()
            require(sha(raw) == expected, f'source SHA changed: {rel}')
            previous = identity[rel]
            require(previous['original_sha256'] == previous['candidate_sha256'] == expected
                    and previous['byte_equal'] is True, f'r2 source identity mismatch: {rel}')
            contents[rel] = raw.decode('ascii')
            report['sources'][rel] = {'path': str(path), 'bytes': len(raw), 'SHA256': expected,
                                      'r2_original_and_candidate_match': True}
        tests = self_test()
        (out / 'synthetic-tests.json').write_text(json.dumps(tests, indent=2), encoding='utf-8')
        top, top_proof, declarations, original_top = make_top(contents[PS_REL])
        wrapper, wrapper_proof = make_wrapper(contents[WRAPPER_REL])
        outputs = {'ps_ai_read_observed.v': top, 'ps_ai_wrapper.sv': wrapper,
                   'original-ps-ai-top.txt': original_top}
        for filename, source in outputs.items():
            raw = source.encode('ascii')
            (out / filename).write_bytes(raw)
            report['outputs'][filename] = {'bytes': len(raw), 'SHA256': sha(raw)}
        proof = {'top': top_proof, 'wrapper': wrapper_proof, 'wire_declarations': declarations,
                 'submodules_reused_from_original_generated_file': True,
                 'BD_XCI_and_source_reference_modified': False,
                 'no_hierarchical_private_reference_added': True}
        (out / 'inverse-proof.json').write_text(json.dumps(proof, indent=2), encoding='utf-8')
        layout = {'bits': 128, 'bytes': 16, 'active_bits': 73, 'reserved_bits': 55,
                  'reserved_hi': 127, 'reserved_lo': 73, 'reserved_value': 0,
                  'fields': [{'signal': 'axi_interconnect_4_M00_AXI_' + field, 'hi': hi, 'lo': lo,
                              'width': hi - lo + 1} for field, hi, lo in FIELDS],
                  'clock_source': 'hp_axi_aclk_1', 'resetn_source': 'proc_sys_reset_1_peripheral_aresetn'}
        (out / 'tap-layout.json').write_text(json.dumps(layout, indent=2), encoding='utf-8')
        for filename, before, after in [('top-diff.patch', original_top, top),
                                        ('wrapper-diff.patch', contents[WRAPPER_REL], wrapper)]:
            patch = ''.join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                                               fromfile='original', tofile='observed'))
            (out / filename).write_bytes(patch.encode('ascii'))
        report['passed'] = top_proof['passed'] and wrapper_proof['passed'] and tests['passed']
        report['actual_wire_width_assertions'] = len(declarations)
        report['remaining_checks'] = ['HDL compile/elaboration', 'actual clock/reset/CDC and timing in new candidate',
                                      'routing/resource review', 'board behavior; no new startup permission implied']
    except Exception as error:
        report['error'] = {'type': type(error).__name__, 'message': str(error)}
    finally:
        report['elapsed_seconds'] = round(time.monotonic() - started, 3)
        (out / 'actual-driver.py').write_bytes(Path(__file__).read_bytes())
        (out / 'review.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        manifest = [{'path': p.name, 'bytes': p.stat().st_size, 'SHA256': sha(p.read_bytes())}
                    for p in sorted(out.iterdir()) if p.is_file()]
        (out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps({'passed': report['passed'], 'elapsed_seconds': report['elapsed_seconds'],
                      'output_directory': str(out), 'error': report.get('error')}))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
