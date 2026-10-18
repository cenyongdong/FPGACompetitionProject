"""Prepare only the existing isolated r3 copy after its monitor unit gate.

No EDA, SDK or board command is run. Original generated PS/BD/XCI and original
AI/DDR logic are protected. A fresh evidence directory and exact inverse edits
make every changed existing source reviewable; an interrupted preparation must
not be rerun into the same directory or used as a successful candidate.
"""
from pathlib import Path
import argparse
import difflib
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tarfile
import time

ROOT = Path(__file__).resolve().parents[3]
E3 = ROOT / 'tools/pose-v1/evidence/hdmi-live-20261017-r3'
REFERENCE = ROOT / '.local/hdmi-live-20261017-r3/reference'
FORMAL = ROOT / 'FPGA/hdmi_candidate'
COPY_MANIFEST = E3 / 'read-reference-copy.json'
SIM_RESULT = E3 / 'sim-ai-read-monitor-r1/result.json'
EXPORTER = FORMAL / 'scripts/prepare_ps_read_taps.py'
DIAGNOSTIC = FORMAL / 'diagnostics/ai_read_monitor.sv'
CDC = FORMAL / 'diagnostics/ai_read_monitor_cdc.tcl'
MODEL_ROOT = ROOT / 'tools/pose-v1/evidence/hdmi-live-20261017-r2/build-shared-monitor-v2'
MUTABLE = ['rtl/ps_ai_peripheral.sv', 'rtl/ps_ai_wrapper.sv',
           'rtl/hdmi_candidate/hdmi_cam_router.sv', 'constrs_1/hdmi_cdc.tcl',
           'constrs_1/hdmi_cdc.xdc', 'ip_patch/process_control/implementation_opt_pre_hdmi.tcl']
ADDED = ['rtl/hdmi_candidate/ps_ai_read_observed.v', 'rtl/hdmi_candidate/ai_read_monitor.sv',
         'constrs_1/ai_read_monitor_cdc.tcl']
BASE, DECODE_LSB, SPAN = 0x400b0400, 9, 512
FIELDS = [('ARADDR',31,0),('ARID',37,32),('ARLEN',41,38),('ARSIZE',44,42),
          ('ARBURST',46,45),('ARLOCK',48,47),('ARCACHE',52,49),('ARPROT',55,53),
          ('ARQOS',59,56),('ARVALID',60,60),('ARREADY',61,61),('RVALID',62,62),
          ('RREADY',63,63),('RID',69,64),('RRESP',71,70),('RLAST',72,72)]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def protected_files(reference):
    """All existing RTL plus original project/BD/IP/configuration identities."""
    files = {}
    for path in reference.rglob('*'):
        if not path.is_file():
            continue
        rel = path.relative_to(reference).as_posix()
        if rel.startswith('rtl/') or path.suffix.lower() in {'.bd', '.xci', '.xpr', '.json',
                                                           '.v', '.sv', '.edif', '.edf', '.xdc', '.tcl'}:
            files[rel] = sha(path.read_bytes())
    return files


def protected_models():
    """Read retained package contents; no extraction, rewrite or deployment."""
    expected = read_json(MODEL_ROOT / 'package-files.json')
    archive = MODEL_ROOT / 'package.tar'
    require(archive.is_file(), 'retained model package missing')
    result = {}
    with tarfile.open(archive, 'r:') as tar:
        for member in tar:
            name = member.name.removeprefix('./')
            if name not in {'models/piw24_shared_ZG.json', 'models/piw24_shared_ZG.raw'}:
                continue
            require(member.isfile() and name not in result, 'invalid/duplicate model archive member')
            data = tar.extractfile(member).read()
            require(sha(data) == expected[name], f'protected model identity changed: {name}')
            result[name] = {'bytes': len(data), 'SHA256': sha(data)}
    require(len(result) == 2, 'both fixed model JSON and RAW required')
    return result


def load_exporter():
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location('ai_read_ps_exporter', EXPORTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def wire_width(source, signal):
    matches = list(re.finditer(r'\bwire\s*(?:\[\s*(\d+)\s*:\s*(\d+)\s*\])?\s*'
                              + re.escape(signal) + r'\s*;', source))
    require(len(matches) == 1, f'unique existing wire required: {signal}')
    match = matches[0]
    return abs(int(match[1])-int(match[2]))+1 if match[1] else 1


def channel_expression(source, prefix):
    widths, expressions = [], []
    for field, hi, lo in FIELDS:
        signal = prefix + field
        width = wire_width(source, signal)
        expected = 5 if field in ('ARID', 'RID') else hi-lo+1
        require(width == expected, f'existing channel width changed: {signal}={width}/{expected}')
        expressions.append("{1'b0," + signal + '}' if field in ('ARID','RID') else signal)
        widths.append(6 if field in ('ARID','RID') else width)
    require(sum(widths) == 73 and sum(widths)+55 == 128, 'channel total width mismatch')
    return "{55'd0," + ','.join(reversed(expressions)) + '}', widths


def peripheral_variant(source, exporter):
    require('ai_read_path_monitor' not in source and 'diagnostic_hp2_read' not in source,
            'peripheral already integrated')
    nl = exporter.newline(source)
    edits = []
    anchor = '  mna_gp_ww_itf ai_diag_csr();'
    require(source.count(anchor) == 1, 'existing CSR declaration anchor changed')
    declarations = nl + '  mna_gp_ww_itf read_diag_passthrough();' + nl
    declarations += '  mna_gp_ww_itf ai_read_csr();' + nl
    declarations += '  wire [127:0] diagnostic_hp2_read;' + nl
    declarations += '  wire diagnostic_hp2_clk,diagnostic_hp2_resetn;' + nl
    declarations += '  wire [767:0] ai_read_channels;' + nl
    at = source.index(anchor)+len(anchor)
    exporter.add_edit(edits, at, at, '', declarations, 'append read observer interfaces and explicit PS taps')
    upstream = '.upstream(cam.slave)'
    require(source.count(upstream) == 1, 'existing v2 router upstream is not unique')
    at = source.index(upstream)
    exporter.add_edit(edits, at, at+len(upstream), upstream,
                      '.upstream(read_diag_passthrough.slave)', 'place new router before retained v2 router')
    instance = re.search(r'\bps_ai_wrapper\s+ps_ai_wrapper_u0\s*\(', source)
    require(instance is not None and len(re.findall(r'\bps_ai_wrapper\s+ps_ai_wrapper_u0\s*\(', source)) == 1,
            'unique existing PS wrapper instance required')
    ports = nl + ''.join(f'    .{port}({port}),' + nl for port in exporter.PORTS)
    exporter.add_edit(edits, instance.end(), instance.end(), '', ports, 'append explicit new output connections')
    lines = ["// Six-boundary passive read observer, own 512-byte CSR aperture.",
             "hdmi_cam_router #(.HDMI_BASE(32'h400b0400),.DECODE_LSB(9)) ai_read_diag_router(",
             ' .clk(gp_clk),.resetn(~gp_clk_rst),.upstream(cam.slave),',
             ' .camera(read_diag_passthrough.master),.hdmi(ai_read_csr.master));']
    lane_widths = {}
    for lane, prefix in enumerate([f'S{i}_AXI_HP_HC_' for i in range(4)] + ['S_AXI_HP2_']):
        expression, widths = channel_expression(source, prefix)
        lane_widths[prefix] = widths
        lines.append(f'assign ai_read_channels[{128*lane}+:128] = {expression};')
    lines += ['assign ai_read_channels[640+:128] = diagnostic_hp2_read;',
              'ai_read_monitor ai_read_path_monitor(',
              ' .source_clk(diagnostic_hp2_clk),.csr_clk(gp_clk),.resetn(sys_rst_n & FCLK_RESET0_N),',
              ' .channels(ai_read_channels),',
              ' .source_flags({pl_rst_n,diagnostic_hp2_resetn,hp_clk_rst,ddr_ui_rst,ddr3_init_done}),',
              ' .csr(ai_read_csr.slave));', '']
    addition = nl + nl.join(lines) + nl
    anchor = '// Passive observer: a second reserved camera alias, independent of HDMI CSR.'
    require(source.count(anchor) == 1, 'v2 observer insertion anchor changed')
    at = source.index(anchor)
    exporter.add_edit(edits, at, at, '', addition, 'append new passive monitor; existing v2 and HDMI blocks unchanged')
    result, proof = exporter.transform(source, edits)
    require(result.count('.upstream(cam.slave)') == 1
            and '.upstream(read_diag_passthrough.slave)' in result
            and '.upstream(diag_passthrough.slave)' in result, 'router chain contract failed')
    require(wire_width(result, 'ai_read_channels') == 768
            and wire_width(result, 'diagnostic_hp2_read') == 128, 'channel aggregate width failed')
    return result, proof, lane_widths


def router_variant(source, exporter):
    require('DECODE_LSB' not in source, 'router already parameterized')
    header = "module hdmi_cam_router #(parameter [31:0] HDMI_BASE=32'h400b0000)("
    require(source.count(header) == 1 and source.count('[31:8]') == 4, 'router decode source contract changed')
    edits = []
    at = source.index(header) + header.index(')(')
    exporter.add_edit(edits, at, at, '', ',parameter integer DECODE_LSB=8', 'append parameter retaining old default')
    for match in re.finditer(re.escape('[31:8]'), source):
        exporter.add_edit(edits, match.start(), match.end(), '[31:8]', '[31:DECODE_LSB]', 'parameterize only existing decode slice')
    result, proof = exporter.transform(source, edits)
    # Exhaustive low16 address offsets cover all three current apertures.
    # High16 remains the unchanged fixed 0x400b and is compared in both models.
    old_windows = [0x400b0000, 0x400b0100]
    default = re.search(r'parameter integer DECODE_LSB=(\d+)', result)
    require(default is not None and int(default[1]) == 8, 'old default decode width was not retained')
    actual_default = int(default[1])
    for low in range(65536):
        address = 0x400b0000 | low
        for base in old_windows:
            require((base <= address < base+256) == (address >> actual_default == base >> actual_default),
                    'default router no longer selects original256B aperture')
        selected = address >> DECODE_LSB == BASE >> DECODE_LSB
        require(selected == (BASE <= address < BASE + SPAN), 'new 512B decode mismatch')
        require(not selected or all(address >> 8 != base >> 8 for base in old_windows), 'new aperture shadows old')
    require(BASE % SPAN == 0, 'new aperture must be512B aligned')
    proof['decode_low16_cases_checked'] = 65536
    proof['old_default_decode_LSB'] = 8
    proof['new_decode_LSB'] = DECODE_LSB
    return result, proof


def scoped_cdc_variant(source, exporter):
    require('ai_read_path_monitor' not in source, 'read observer CDC exclusion already present')
    pairs = [
        ('{NAME !~ U0_ps_ai_peripheral/hdmi_display/* && NAME !~ U0_ps_ai_peripheral/ai_path_monitor/*}',
         '{NAME !~ U0_ps_ai_peripheral/hdmi_display/* && NAME !~ U0_ps_ai_peripheral/ai_path_monitor/* && NAME !~ U0_ps_ai_peripheral/ai_read_path_monitor/*}'),
        ('{NAME =~ U0_ps_ai_peripheral/hdmi_display/* || NAME =~ U0_ps_ai_peripheral/ai_path_monitor/*}',
         '{NAME =~ U0_ps_ai_peripheral/hdmi_display/* || NAME =~ U0_ps_ai_peripheral/ai_path_monitor/* || NAME =~ U0_ps_ai_peripheral/ai_read_path_monitor/*}'),
    ]
    edits = []
    for old, new in pairs:
        require(source.count(old) == 1, 'original scoped clock-pair exclusion changed')
        at = source.index(old)
        exporter.add_edit(edits, at, at+len(old), old, new, 'exclude only new read observer from old clock-pair cuts')
    return exporter.transform(source, edits)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, default=REFERENCE)
    parser.add_argument('--evidence-directory', type=Path, default=E3 / 'read-candidate-preparation')
    args = parser.parse_args()
    reference, evidence = args.reference.resolve(), args.evidence_directory.resolve()
    require(reference == REFERENCE.resolve(), 'only the prepared isolated r3 reference may be modified')
    require(evidence.parent == E3.resolve() and not evidence.exists(), 'fresh r3 evidence directory required')
    # Required gates precede all source mutations and PS text generation.
    sim_raw = SIM_RESULT.read_bytes()
    require(json.loads(sim_raw)['passed'] is True, 'read-monitor unit simulation gate not passed')
    simulated_monitor = (SIM_RESULT.parent / 'ai_read_monitor.sv').read_bytes()
    require(DIAGNOSTIC.read_bytes() == simulated_monitor, 'monitor source differs from actual unit-simulation snapshot')
    copied_raw = COPY_MANIFEST.read_bytes()
    copied = json.loads(copied_raw)
    require(Path(copied['new_reference']).resolve() == reference and copied['frozen_sources_checked'] == 474,
            'isolated reference copy identity gate failed')
    require(reference.is_dir(), 'isolated reference absent')
    for rel in ADDED:
        require(not (reference / rel).exists(), f'new source already present: {rel}')
    for row in copied['RTL_before_any_new_integration']:
        require(sha((reference / row['path']).read_bytes()) == row['sha256'], f'copied RTL changed before integration: {row["path"]}')
    exporter = load_exporter()
    evidence.mkdir()
    started = time.monotonic()
    report = {'passed': False, 'reference': str(reference), 'working_directory': str(Path.cwd()),
              'parameters': {'CSR_base': hex(BASE), 'span_bytes': SPAN, 'decode_LSB': DECODE_LSB,
                             'channels': 6, 'channel_bits': 128, 'channel_total_bits': 768},
              'unit_gate': {'path': str(SIM_RESULT), 'SHA256': sha(sim_raw), 'passed': True,
                            'monitor_source_SHA256':sha(simulated_monitor),'actual_source_bytes_match':True},
              'copy_manifest_SHA256': sha(copied_raw), 'EDA_or_board_access': False,
              'reference_mutation_started': False,
              'failure_stop': 'retain all original/new bytes and partial tree; no EDA or repeated integration',
              'protected_before': {}, 'protected_after': {}}
    try:
        (evidence / 'unit-result.json').write_bytes(sim_raw)
        (evidence / 'copy-manifest.json').write_bytes(copied_raw)
        before = protected_files(reference)
        report['protected_before'] = before
        models_before = protected_models()
        original = {rel: (reference / rel).read_bytes() for rel in MUTABLE}
        require(original['constrs_1/hdmi_cdc.tcl'] == original['constrs_1/hdmi_cdc.xdc'], 'old Tcl/XDC copies differ')
        for rel, raw in original.items():
            backup = evidence / 'before' / rel
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_bytes(raw)
        run = subprocess.run([sys.executable, str(EXPORTER), '--source-reference', str(reference),
                              '--output-directory', str(evidence / 'ps-export')],
                             cwd=ROOT, capture_output=True, timeout=30)
        (evidence / 'ps-export.stdout.txt').write_bytes(run.stdout)
        (evidence / 'ps-export.stderr.txt').write_bytes(run.stderr)
        require(run.returncode == 0 and read_json(evidence / 'ps-export/review.json')['passed'], 'PS text export failed')
        layout = read_json(evidence / 'ps-export/tap-layout.json')
        require(layout['bits'] == 128 and layout['active_bits'] == 73 and layout['reserved_bits'] == 55,
                'PS tap bus width contract changed')
        require([(x['signal'].removeprefix('axi_interconnect_4_M00_AXI_'),x['hi'],x['lo'])
                 for x in layout['fields']] == FIELDS, 'PS tap field layout changed')
        planned, proofs = {}, {}
        planned['rtl/ps_ai_wrapper.sv'] = (evidence / 'ps-export/ps_ai_wrapper.sv').read_bytes()
        planned['rtl/hdmi_candidate/ps_ai_read_observed.v'] = (evidence / 'ps-export/ps_ai_read_observed.v').read_bytes()
        peripheral, proof, widths = peripheral_variant(original['rtl/ps_ai_peripheral.sv'].decode('ascii'), exporter)
        planned['rtl/ps_ai_peripheral.sv'] = peripheral.encode('ascii')
        proofs['peripheral'] = proof
        router, proof = router_variant(original['rtl/hdmi_candidate/hdmi_cam_router.sv'].decode('ascii'), exporter)
        planned['rtl/hdmi_candidate/hdmi_cam_router.sv'] = router.encode('ascii')
        proofs['router'] = proof
        for rel in ['constrs_1/hdmi_cdc.tcl','constrs_1/hdmi_cdc.xdc']:
            cdc, proof = scoped_cdc_variant(original[rel].decode('ascii'), exporter)
            planned[rel] = cdc.encode('ascii')
            proofs[rel] = proof
        hook_rel = 'ip_patch/process_control/implementation_opt_pre_hdmi.tcl'
        hook = original[hook_rel].decode('ascii')
        require('ai_read_monitor_cdc.tcl' not in hook and hook.count('constrs_1/ai_monitor_cdc.tcl') == 1,
                'original v2 hook changed or new hook already installed')
        suffix = exporter.newline(hook) + 'source [file normalize [file join [file dirname [info script]] ../../constrs_1/ai_read_monitor_cdc.tcl]]' + exporter.newline(hook)
        new_hook, proof = exporter.transform(hook, [{'start':len(hook),'end':len(hook),'old':'','new':suffix,
                                                     'reason':'append new observer CDC after unchanged HDMI/v2 hooks'}])
        planned[hook_rel] = new_hook.encode('ascii')
        proofs['hook'] = proof
        monitor_raw, cdc_raw = DIAGNOSTIC.read_bytes(), CDC.read_bytes()
        monitor = monitor_raw.decode('ascii')
        require(re.search(r'input\s+wire\s*\[767:0\]\s*channels', monitor)
                and re.search(r'input\s+wire\s*\[4:0\]\s*source_flags', monitor)
                and 'WORDS=104' in monitor, 'monitor port/word contract changed')
        planned['rtl/hdmi_candidate/ai_read_monitor.sv'] = monitor_raw
        planned['constrs_1/ai_read_monitor_cdc.tcl'] = cdc_raw
        require(set(planned) == set(MUTABLE + ADDED), 'unexpected planned file set')
        (evidence / 'inverse-proof.json').write_text(json.dumps(proofs, indent=2), encoding='utf-8')
        (evidence / 'channel-widths.json').write_text(json.dumps({'fields':FIELDS,'lane_widths':widths,
                                                                 'five_padded_ID_lanes':True,'PS_M00_ID_bits':6,
                                                                 'channels_bits':768,'flags_bits':5}, indent=2), encoding='utf-8')
        changes = []
        for rel, raw in planned.items():
            stage = evidence / 'after' / rel
            stage.parent.mkdir(parents=True, exist_ok=True)
            stage.write_bytes(raw)
            old = original.get(rel, b'')
            patch = ''.join(difflib.unified_diff(old.decode('ascii').splitlines(keepends=True),
                                               raw.decode('ascii').splitlines(keepends=True),
                                               fromfile=rel+'.before',tofile=rel+'.after'))
            diff = evidence / 'diff' / (rel + '.patch')
            diff.parent.mkdir(parents=True, exist_ok=True)
            diff.write_bytes(patch.encode('ascii'))
            changes.append({'path':rel,'before_SHA256':sha(old) if rel in original else None,
                            'after_SHA256':sha(raw),'bytes':len(raw)})
        report['planned_changes'] = changes
        require(protected_files(reference) == before, 'reference changed concurrently during preparation')
        report['reference_mutation_started'] = True
        for rel, raw in planned.items():
            (reference / rel).write_bytes(raw)
        after = protected_files(reference)
        report['protected_after'] = after
        changed = sorted(rel for rel, digest in before.items() if after.get(rel) != digest)
        expected_changed = sorted(rel for rel in MUTABLE if rel in before)
        require(changed == expected_changed, f'protected file changes exceed whitelist: {changed}')
        require(sorted(set(after)-set(before)) == sorted(ADDED),
                'unexpected added protected sources')
        for rel, raw in planned.items():
            require((reference / rel).read_bytes() == raw, f'written source readback mismatch: {rel}')
        require(before[exporter.PS_REL] == after[exporter.PS_REL], 'original generated PS changed')
        models_after = protected_models()
        require(models_after == models_before, 'fixed model/RAW identity changed')
        report.update({'passed':True, 'protected_changed_whitelist':changed,
                       'original_AI_DDR_BD_XCI_XPR_and_other_existing_sources_unchanged':True,
                       'fixed_models_before':models_before,'fixed_models_after':models_after,
                       'source_monitor_SHA256':sha(monitor_raw),'source_CDC_SHA256':sha(cdc_raw),
                       'HDL_files_not_added_to_XPR':ADDED[:2],
                       'remaining_checks':['elaboration/source registration','actual six-boundary clock/reset taps',
                                           'CDC/snapshot max-delay/STA/DRC','board release authorization']})
    except Exception as error:
        report['error'] = {'type':type(error).__name__,'message':str(error)}
    finally:
        report['seconds'] = round(time.monotonic()-started,3)
        (evidence / 'actual-driver.py').write_bytes(Path(__file__).read_bytes())
        (evidence / 'review.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        manifest = [{'path':p.relative_to(evidence).as_posix(),'bytes':p.stat().st_size,'SHA256':sha(p.read_bytes())}
                    for p in sorted(evidence.rglob('*')) if p.is_file()]
        (evidence / 'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({'passed':report['passed'],'seconds':report['seconds'],'error':report.get('error')}))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
