"""Gate actual r5 checkpoint-only routed reports, preserving only the two prior AI exceptions.

No EDA, device access, source mutation, new exception or BOOT permission. A
successful result permits only offline diagnostic bit generation; full CDC and
board/inference/HDMI acceptance remain separate.
"""
from pathlib import Path
import collections
import hashlib
import importlib.util
import json
import math
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
E3 = ROOT / 'tools/pose-v1/evidence/hdmi-live-20261017-r3'
REFERENCE = ROOT / '.local/hdmi-live-20261017-r3/reference'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def finite_number(value):
    number = float(value)
    require(math.isfinite(number), f'nonfinite report number: {value}')
    return number


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    directory = E3 / 'read-v3r5-reports'
    require(not (directory / 'review.json').exists(), 'refusing to overwrite route review')
    for stage in ['read-v3r5-bootstrap', 'read-v3r5-route', 'read-v3r5-reports']:
        execution = load(E3 / stage / 'execution.json')
        require(execution['exit'] == 0 and not execution.get('stopped_by_monitor', False)
                and not execution.get('timeout', False), f'actual EDA stage failed/stopped: {stage}')
        require(load(E3 / stage / 'phase-review.json')['passed'] is True,
                f'checkpoint continuation phase post-check failed: {stage}')
    physical = E3 / 'checkpoints-before-route-r4/ai7030_edif_top_physopt.dcp'
    physical_sha = 'f58a5f8e6f432be7e656de5ee32eae5ae63b491d5a5cb1055425ee32895525d9'
    require(physical.stat().st_size == 44506212
            and hashlib.sha256(physical.read_bytes()).hexdigest() == physical_sha,
            'frozen completed r4 physical checkpoint changed')
    predecessor = load(E3 / 'read-v3r4-route/execution.json')
    require(predecessor['exit'] == 1 and predecessor['stopped_by_monitor'] is True,
            'r4 hard-timeout predecessor must remain a stopped run, not an acceptance')
    routed_identity = load(E3 / 'read-v3r5-route/routed-checkpoint.json')
    routed_path = REFERENCE / 'fpai_demo_vivado.runs/route_read_v3r5/ai7030_edif_top_routed.dcp'
    require(Path(routed_identity['path']).resolve() == routed_path.resolve()
            and routed_identity['source_physical_checkpoint_SHA256'] == physical_sha
            and routed_path.stat().st_size == routed_identity['bytes']
            and hashlib.sha256(routed_path.read_bytes()).hexdigest() == routed_identity['SHA256'],
            'actual r5 routed checkpoint identity/lineage differs')
    gate = load(E3 / 'read-v3r3-constraints-r3/review.json')
    require(gate['route_prerequisite_pass'], 'r3 constraint gate failed')
    sys.dont_write_bytecode = True
    helpers_path = Path(__file__).with_name('review_ai_read_constraints.py')
    spec = importlib.util.spec_from_file_location('ai_read_constraint_helpers', helpers_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    require(gate['review_driver_SHA256'] == helper.digest(helpers_path),
            'constraint helper changed since actual constraints review')
    require(helper.stable_sources() == gate['source_sha256'],
            'managed candidate source identity map changed after constraints')
    require(helper.managed_ps_identity() == gate['managed_PS_source_identity'],
            'managed PS source proof changed after constraints')
    require(helper.compile_dependency_identity() == gate['actual_managed_PS_compile_dependencies'],
            'actual managed PS compile dependency proof changed after constraints')
    sources = gate['source_sha256']
    for rel, expected in sources.items():
        require(hashlib.sha256((REFERENCE / rel).read_bytes()).hexdigest() == expected,
                f'stable source changed after constraints: {rel}')
    installed_path = ROOT / 'tools/pose-v1/evidence/hdmi-live-20261017-r2/toolchain-identity-review.json'
    installed = load(installed_path)
    require(installed.get('matching') is True and installed.get('checked_files') == 41
            and len(installed['actual']) == 41, 'installed-library ledger incomplete')
    toolchain = Path('D:/vivado18.3/Vivado/2018.3')
    for relative, expected in installed['actual'].items():
        actual = (toolchain / relative).resolve()
        require(actual.is_relative_to(toolchain.resolve())
                and hashlib.sha256(actual.read_bytes()).hexdigest() == expected,
                'installed library identity changed: ' + relative)
    proof_hashes = {}
    for mode in ['bootstrap', 'route', 'reports']:
        phase_dir = E3 / ('read-v3r5-' + mode)
        phase = load(phase_dir / 'phase-review.json')
        require(phase.get('mode') == mode and phase.get('source_identity_unchanged') is True
                and phase.get('no_managed_run_status_used_or_fabricated') is True
                and phase.get('read_bits') == 2768, 'phase identity/mode differs: ' + mode)
        proof = load(phase_dir / 'input-proof.json')
        require(proof['gate_SHA256'] == hashlib.sha256((E3 / 'read-v3r3-constraints-r3/review.json').read_bytes()).hexdigest()
                and proof['source_sha256'] == sources
                and proof['installed_identity_ledger_SHA256'] == hashlib.sha256(installed_path.read_bytes()).hexdigest()
                and proof['installed_sha256'] == installed['actual']
                and proof['checkpoint_SHA256'] == physical_sha
                and proof['original_native_SHA256'] == 'fe2a27e53a4131a1503d5e28dea02a79dceaef954d56bf3912a56b642a91269a'
                and proof['parent_synthesis_provenance'] == 'synth_read_v3r3'
                and Path(proof['native_directory']).resolve() == routed_path.parent.resolve(),
                'phase input identity chain differs: ' + mode)
        proof_hashes[mode] = {name: hashlib.sha256((phase_dir / name).read_bytes()).hexdigest()
                              for name in ['execution.json', 'phase-review.json', 'input-proof.json']}
    native = REFERENCE / 'fpai_demo_vivado.runs/route_read_v3r5'
    require((native / '.route_design.end.rst').is_file(), 'actual r5 native route completion absent')
    timing = (directory / 'timing-summary.rpt').read_text()
    lines = timing.splitlines()
    header = next(i for i, line in enumerate(lines) if line.startswith('    WNS(ns)'))
    values = lines[header+2].split()
    require(len(values) == 12, 'unrecognized global timing summary')
    wns, tns, whs, ths, wpws, tpws = [finite_number(values[i]) for i in [0,1,4,5,8,9]]
    require(wns >= 0 and whs >= 0 and tns == ths == 0, 'new setup/hold violation')
    require(values[2] == values[6] == '0' and values[10] == '2', 'unexpected failing endpoint count')
    require(wpws == -.409 and tpws == -.479, 'pulse-width violations differ from accepted AI model objects')
    require('There are 0 register/latch pins with no clock.' in timing
            and 'There are 0 pins that are not constrained for maximum delay.' in timing,
            'unclocked/unconstrained timing endpoints')
    pulse = [line for line in (native / 'ai7030_edif_top_timing_summary_routed.rpt').read_text().splitlines()
             if line.startswith('Min Period') and re.search(r'\s-0\.', line)]
    require(len(pulse) == 2, 'accepted AI pulse exception count changed')
    prefix = 'U0_ps_ai_peripheral/ZGolo/u_AI_Mate_top/clkrst_wrapper_u0/AI_CORE_CLK/inst/'
    for endpoint, required, slack in [('clkout1_buf/I','1.409','-0.409'),
                                      ('plle2_adv_inst/CLKOUT0','1.071','-0.071')]:
        matches = [line for line in pulse if line.endswith(prefix+endpoint)]
        fields = matches[0].split() if len(matches) == 1 else []
        pin_kind = 'BUFG/I' if endpoint == 'clkout1_buf/I' else 'PLLE2_ADV/CLKOUT0'
        require(len(fields) == 10 and fields[:5] == ['Min', 'Period', 'n/a', pin_kind, 'n/a']
                and finite_number(fields[5]) == float(required)
                and finite_number(fields[6]) == 1.000 and finite_number(fields[7]) == float(slack)
                and fields[-1] == prefix+endpoint,
                f'accepted AI exception object/model changed: {endpoint}')
    drc = (native / 'ai7030_edif_top_drc_routed.rpt').read_text()
    require(not re.findall(r'^\S+#\d+ Error$', drc, re.MULTILINE), 'factory DRC profile has errors')
    require('REQP-1580#' not in drc and 'UTLZ-1#' not in drc, 'device/library/utilization DRC violation')
    disabled = re.findall(r'^The following rules are disabled: ([^\r\n]+)', drc, re.MULTILINE)
    require(disabled == ['REQP-44, REQP-46, REQP-52, REQP-56'], 'factory DRC profile changed')
    reopened = (directory / 'DRC-reopened-default-profile.rpt').read_text()
    errors = re.findall(r'^(\S+#\d+) Error$', reopened, re.MULTILINE)
    require(errors == ['REQP-52#1','REQP-56#1'], f'default-profile DRC errors changed: {errors}')
    status = (directory / 'route-status.rpt').read_text()
    require(re.search(r'# of nets with routing errors\.+\s*:\s*0\s*:', status), 'routing errors/nonrecognized status')
    require('VIOLATED' not in (directory / 'bus-skew.rpt').read_text(), 'bus skew violation')
    bounds = (directory / 'snapshot-routed-bounds.txt').read_text().splitlines()
    require(len(bounds) == 3, 'retained snapshot bound rows missing')
    for row, name, expected in zip(bounds, ['observer','command','response'], [10.,5.,10.]):
        require(row.startswith(name+'|'), 'retained snapshot scope mismatch')
        requirement = finite_number(re.search(r'requirement=([\d.-]+)', row)[1])
        slack = finite_number(re.search(r'slack=([\d.-]+)', row)[1])
        require(requirement == expected and slack >= 0, f'retained snapshot bound failed: {name}')
        for ce in (directory / f'snapshot-{name}-CE.txt').read_text().splitlines():
            require(finite_number(re.search(r'requirement=([\d.-]+)', ce)[1]) == expected
                    and finite_number(re.search(r'slack=([\d.-]+)', ce)[1]) >= 0,
                    f'retained snapshot enable timing failed: {name}')
    command_ce = (directory / 'snapshot-command-CE.txt').read_text().splitlines()
    require(len(command_ce) == 96, 'HDMI command CE path set changed/incomplete')
    for scope in ['observer', 'HDMI', 'read']:
        for kind in ['setup', 'hold']:
            report = (directory / f'{scope}-{kind}.rpt').read_text()
            require('VIOLATED' not in report and 'Slack (MET)' in report,
                    f'{scope} {kind} report absent or violated')
    old = helper.monitor_cdc(directory / 'observer-CDC.rpt', helper.OLD_SCOPE,
                             gate['retained_v2_indices'], False)
    require(len(old['payload_indices']) == gate['retained_v2_bits'] == 708, 'retained v2 bank changed')
    read = helper.monitor_cdc(directory / 'read-CDC.rpt', helper.READ_SCOPE,
                              gate['read_indices'], True)
    require(len(read['payload_indices']) == gate['read_bits'], 'read bank optimization/endpoint set changed after constraints')
    # Full generic CDC reports remain intact; these intentional HDMI held-data
    # CDC-1 rows keep the existing payload-specific manual-review boundary.
    all_rows = helper.cdc_rows(directory / 'CDC.rpt')
    hdmi_rows = [line for line in all_rows if '/hdmi_display/' in line]
    require(hdmi_rows, 'HDMI CDC rows missing')
    for row in hdmi_rows:
        if re.search(r'\bCDC-1\s', row):
            require('/mailbox/payload_hold_reg' in row, 'new unexplained HDMI Critical CDC-1')
        else:
            require(re.search(r'\bCDC-(3|6|10|12|15)\s', row), f'unrecognized HDMI CDC structure: {row}')
    physical = (directory / 'HDMI-clock-physical.txt').read_text()
    require(physical.count('|OSERDESE2|') == 8, 'HDMI serializer count changed')
    require(physical.count('/CLK|serial_raw') == physical.count('/CLKDIV|pixel_clk') == 8,
            'HDMI serializer physical clock branches changed')
    require(all(marker in physical for marker in ['|BUFIO|','|BUFR|','|MMCME2_ADV|']),
            'HDMI physical clock resources incomplete')
    read_bounds = (directory / 'read-snapshot-routed.txt').read_text()
    fields = dict(re.findall(r'(\w+)=([^|\s]+)', read_bounds))
    require(finite_number(fields['requirement']) == 10. and finite_number(fields['slack']) >= 0,
            'routed read held-bus worst-path bound failed')
    require(int(fields['source_bits']) == int(fields['capture_bits']) == gate['read_bits'],
            'routed read source/capture count changed')
    indices = helper.parse_indices((directory / 'read-snapshot-indices.txt').read_text(),
                                   source_key='source', capture_key='capture')
    require(indices == gate['read_indices'], 'routed read source/capture bit set changed')
    endpoints = helper.snapshot_endpoints(directory / 'read-snapshot-endpoints.txt', indices)
    clocks = helper.clock_taps(directory / 'clock-taps.txt', indices)
    require(clocks['source_period_ns'] == 5. and clocks['csr_period_ns'] == 10., 'routed source/CSR period contract failed')
    read_timing = (directory / 'read-snapshot.rpt').read_text()
    require('VIOLATED' not in read_timing and re.search(r'Requirement:\s+10\.000ns', read_timing)
            and 'Slack (MET)' in read_timing, 'routed read snapshot timing report failed/absent')
    review = {'bit_generation_prerequisite_pass':True,
              'candidate_run':'route_read_v3r5','managed_run':False,
              'checkpoint_continuation':{'source_physical_SHA256':physical_sha,
                  'routed_checkpoint':routed_identity,'original_r4_stopped_result_preserved':True,
                  'no_managed_run_status_used_or_fabricated':True},
              'scope':'offline diagnostic candidate only; no whole-system or board acceptance',
              'global_setup_WNS_ns':wns,'global_hold_WHS_ns':whs,'TNS_ns':tns,'THS_ns':ths,
              'raw_timing_pass':False,'unchanged_user_exception_MinPeriod_rows':pulse,
              'retained_snapshot_bounds':bounds,'HDMI_command_CE_paths':len(command_ce),
              'retained_v2_CDC':old,'read_CDC':read,'read_bits':gate['read_bits'],
              'read_snapshot_endpoints':endpoints,'actual_clock_taps':clocks,
              'HDMI_CDC_row_counts':dict(collections.Counter(re.search(r'CDC-\d+',row)[0] for row in hdmi_rows)),
              'factory_DRC_profile_errors':0,'reopened_default_profile_errors_retained':errors,
              'warnings_retained':True,'new_timing_or_DRC_waiver':False,
              'new_BOOT_or_reboot_authorized':False,'source_sha256':sources,
              'setup_XPR_identity_and_route_revision':helper.setup_xpr_identity(),
              'managed_PS_source_identity':gate['managed_PS_source_identity'],
              'actual_managed_PS_compile_dependencies':gate['actual_managed_PS_compile_dependencies'],
              'review_driver_SHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'constraint_helper_SHA256':hashlib.sha256(helpers_path.read_bytes()).hexdigest(),
              'installed_library_identity':{'ledger_SHA256':hashlib.sha256(installed_path.read_bytes()).hexdigest(),
                  'files':installed['actual']}, 'actual_phase_identity_evidence_SHA256':proof_hashes}
    (directory / 'review.json').write_text(json.dumps(review,indent=2),encoding='utf-8')
    print(json.dumps({key:review[key] for key in ['bit_generation_prerequisite_pass','global_setup_WNS_ns',
                                                 'global_hold_WHS_ns','read_bits','actual_clock_taps']},indent=2))


if __name__ == '__main__':
    main()
