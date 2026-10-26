"""Build an uninstrumented derivative of the qualified r45 hardware.

Only the added observation/control fabric is removed. Functional AXI,
HP2 readiness, HDMI error handling and STOP/drain remain unchanged.
"""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'sources'
WORK = ROOT / '.local/hdmi-probe-free-20261025-r1'
EVIDENCE = ROOT / 'tools/pose-v1/evidence/hdmi-probe-free-20261025-r1'
OLD = ROOT / '.local/hp2-deferred-consume-20261024-r45'
OLD_E = ROOT / 'tools/pose-v1/evidence/hp2-deferred-consume-20261024-r45'
BASE = ROOT / 'FPGA/hdmi_candidate/diagnostics/deferred_consume_r45/sources'
SUPPORT = ROOT / 'FPGA/hdmi_candidate/baselines/ps_release_r26/sources'
OLD_REPO = 'C:/Users/cenyongdong/.codex/worktrees/hdmi-s01-isolation/FPGACompetitionProject'


def put(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8', newline='\n')


def remap(text):
    return text.replace(OLD.as_posix(), WORK.as_posix()).replace(OLD_E.as_posix(), EVIDENCE.as_posix()).replace(OLD_REPO, ROOT.as_posix())


def main():
    if (EVIDENCE / 'synthesis-process.json').exists():
        raise RuntimeError('Preserve the active/completed build; do not prepare over it')
    SOURCE.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / 'physical').mkdir(parents=True, exist_ok=True)
    text = (BASE / 'ps_ai_peripheral.sv').read_text()
    begin = text.index('// r37: S01 HDMI')
    end = text.index("hdmi_cam_router #(.HDMI_BASE(32'h400b0000)) hdmi_router", begin)
    text = text[:begin] + '// Uninstrumented S01: only the functional HDMI reader owns RREADY.\nwire hdmi_reader_rready;\nassign S_AXI_HP2_RREADY = hdmi_reader_rready;\n\n' + text[end:]
    text = text.replace('.upstream(diag_passthrough.slave)', '.upstream(cam.slave)')
    text = '\n'.join(line for line in text.splitlines() if not re.search(r'diagnostic_|ai_read_channels|mna_gp_ww_itf (?:diag_passthrough|ai_diag_csr|read_diag_passthrough|ai_read_csr)', line)) + '\n'
    put(SOURCE / 'ps_ai_peripheral.sv', text)

    text = (BASE / 'ps_ai_wrapper.sv').read_text()
    text = '\n'.join(line for line in text.splitlines() if 'diagnostic_' not in line) + '\n'
    text = re.sub(r',\s*\);', '\n);', text)
    put(SOURCE / 'ps_ai_wrapper.sv', text)

    text = (BASE / 'ps_ai.v').read_text()
    begin = text.index('module ps_ai\n')
    end = text.index(');', begin)
    header = text[begin:end]
    header = re.sub(r'\s*diagnostic_\w+\s*,?', '', header)
    header = header.rstrip().rstrip(',')
    text = text[:begin] + header + text[end:]
    text = re.sub(r'^\s*output[^;\n]*diagnostic_[^;\n]*;\n', '', text, flags=re.M)
    text = text.replace('.S_AXI_HP2_ARESETN(diagnostic_ps_resetn)', '.S_AXI_HP2_ARESETN()')
    begin = text.index('  assign diagnostic_hp2_write[31:0]')
    end = text.index('endmodule', begin)
    text = text[:begin] + text[end:]
    text = re.sub(r'\(\*\s*(?:DEBUG\s*=\s*"true"|MARK_DEBUG(?:\s*=\s*"true")?)\s*\*\)\s*', '', text)
    put(SOURCE / 'ps_ai.v', text)

    removed = ('ai_path_monitor', 'ai_read_path_monitor', 'hp2_cycle_recorder', 'hp2_protocol_recorder', 'hp2_protocol_observer', 'deferred_control', 'startup_drain')
    for name in ('hdmi_cdc.tcl', 'ps_release_factory_clocks.tcl'):
        text = (BASE / name).read_text()
        for instance in removed:
            text = text.replace(' && NAME !~ U0_ps_ai_peripheral/' + instance + '/*', '')
            text = text.replace(' || NAME =~ U0_ps_ai_peripheral/' + instance + '/*', '')
        put(SOURCE / name, text)

    text = remap((OLD_E / 'synthesis.tcl').read_text())
    omitted = ('hp2_native_protocol_checker', 'hp2_deferred_control.sv', 'hp2_startup_drain.sv', 'registered-observer.sv', 'hp2_protocol_trace.sv', 'hp2_cycle_trace.sv', 'ps_release_witness.sv', 'ai_boot_witness.sv', 'ai_event_monitor.sv', 'ai_read_monitor.sv')
    text = '\n'.join(line for line in text.splitlines() if not any(name in line for name in omitted)) + '\n'
    for name in ('ps_ai_peripheral.sv', 'ps_ai_wrapper.sv', 'ps_ai.v'):
        text = text.replace((WORK / 'sources' / name).as_posix(), (SOURCE / name).as_posix())
    put(EVIDENCE / 'synthesis.tcl', text)

    text = remap((OLD_E / 'opt.tcl').read_text())
    text = text.replace((WORK / 'sources/ps_release_factory_clocks.tcl').as_posix(), (SOURCE / 'ps_release_factory_clocks.tcl').as_posix())
    begin = text.index('source {' + (WORK / 'sources/pre-opt.tcl').as_posix())
    end = text.index('opt_design\n', begin)
    text = text[:begin] + 'source {' + (SUPPORT / 'implementation_opt_pre.tcl').as_posix() + '}\nsource {' + (SOURCE / 'hdmi_cdc.tcl').as_posix() + '}\n' + text[end:]
    text = text.replace('general.maxThreads 1', 'general.maxThreads 2')
    put(EVIDENCE / 'opt.tcl', text)

    text = remap((OLD_E / 'place-r2.tcl').read_text())
    begin = text.index('set deferred_unplaced_coverage_only')
    end = text.index('# Reapply', begin)
    text = text[:begin] + text[end:]
    text = text.replace('pipeline-opt-clean.dcp', 'pipeline-opt.dcp')
    text = text.replace('D:/FPGACompetitionProject/.local/hp2-bounded-drain-20261024-r38/pipeline-refined.dcp', (OLD / 'pipeline-routed.dcp').as_posix())
    text = text.replace('/pipeline-physical/', '/physical/')
    put(EVIDENCE / 'place.tcl', text)

    text = remap((OLD_E / 'route.tcl').read_text())
    text = '\n'.join(line for line in text.splitlines() if 'startup_drain_bounds.tcl' not in line) + '\n'
    text = text.replace('if {[catch {route_design', 'source {'+(HERE/'strip_probe_attributes.tcl').as_posix()+'}\nif {[catch {route_design')
    text = text.replace('/pipeline-physical/', '/physical/')
    put(EVIDENCE / 'route.tcl', text)
    (EVIDENCE / 'pipeline-physical').mkdir(exist_ok=True)
    state = dict(status='source_prepared', authorization='2026-10-25 user requested removing all inspection probes/protocol checkers and startup reliability validation', removed=list(removed), functional_axi_unchanged=True, hp2_readiness_unchanged=True, hdmi_stop_drain_unchanged=True, candidate_starts=0, SDK_Open=0, original_fallbacks=0, boot_installed=False)
    put(EVIDENCE / 'state.json', json.dumps(state, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(state, ensure_ascii=False))


if __name__ == '__main__':
    main()
