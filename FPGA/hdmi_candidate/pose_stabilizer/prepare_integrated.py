"""Add the existing 1/4-lane filter to the qualified probe-free/drain design.

Prepare isolated sources and incremental build stages; do not touch the board.
No old compact-guard admission or removed diagnostic register map is restored.
"""
from pathlib import Path
import argparse
import json

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = ROOT / 'FPGA/hdmi_candidate/probe_free_drain'
OLD = ROOT / '.local/hdmi-probe-free-drain-20261026-r1'
OLD_E = ROOT / 'tools/pose-v1/evidence/hdmi-probe-free-drain-20261026-r1'

def prepare_finish(work):
    """Reuse baseline physical checks with the actual new inputs and stages."""
    evidence = work / 'reports'
    qualify = (BASE / 'qualify.py').read_text().replace('parents[3]', 'parents[2]')
    qualify = qualify.replace('HERE = Path(__file__).resolve().parent', "HERE = ROOT / 'FPGA/hdmi_candidate/probe_free_drain'")
    qualify = qualify.replace("ROOT / '.local/hdmi-probe-free-drain-20261026-r1'", 'Path(__file__).resolve().parent')
    qualify = qualify.replace("ROOT / 'tools/pose-v1/evidence/hdmi-probe-free-drain-20261026-r1'", "WORK / 'reports'")
    qualify = qualify.replace("('synthesis', 'opt', 'place', 'route', 'scope_fix', 'report_final')", "('synthesis', 'opt-linked' if (E/'opt-linked-execution.json').exists() else 'opt', 'place', 'route', 'report')")
    qualify = qualify.replace('pipeline-scoped.dcp', 'pipeline-routed.dcp')
    start = qualify.index('    sources = ')
    end = qualify.index('\n    result = ', start)
    qualify = qualify[:start] + '''    sources = [p for p in (HERE/'sources').iterdir() if not (WORK/'sources'/p.name).exists()]
    sources += list((WORK/'sources').iterdir())
    sources += [HERE/'strip_probe_attributes.tcl'] + [E/(name+'.tcl') for name in ('synthesis','opt-linked' if (E/'opt-linked-execution.json').exists() else 'opt','place','route','report')]
    filter_timing = [row for row in facts if row[0]=='FILTER_TIMING']
    need({row[1] for row in filter_timing}=={'max','min'} and all(float(row[-1])>=0 for row in filter_timing), 'Filter setup/hold missing/failing')
    def resources(report):
        lines = report.read_text().splitlines()
        def amount(label):
            for line in lines:
                fields=[v.strip().rstrip('*') for v in line.split('|')]
                if len(fields)>2 and fields[1].strip()==label:
                    return float(fields[2].replace(',',''))
            raise RuntimeError('Missing resource field: '+label)
        return dict(LUT=amount('Slice LUTs'),FF=amount('Slice Registers'),DSP=amount('DSPs'),BRAM36=amount('Block RAM Tile'),Slice=amount('Slice'))
    filter_resources=resources(R/'filter-utilization.rpt')
    total_resources=resources(R/'total-utilization.rpt')
    manifest=json.loads((WORK/'manifest.json').read_text())
    within_budget=all(filter_resources[k]<=v for k,v in manifest['budgets'].items())
    need(within_budget,'Filter exceeds the relaxed implementation budget')
''' + qualify[end:]
    qualify = qualify.replace('board_tested=False)', "board_tested=False, hardware_profile=manifest['profile'], lanes=manifest['lanes'], filter_resources=filter_resources, total_resources=total_resources, filter_budget_pass=within_budget)")
    compile(qualify, 'qualify.py', 'exec')
    (work / 'qualify.py').write_text(qualify, newline='\n')
    def remap(text):
        return text.replace(OLD.as_posix(),work.as_posix()).replace(OLD_E.as_posix(),evidence.as_posix()).replace('pipeline-scoped.dcp','pipeline-routed.dcp').replace('impl_probe_free_drain_r1','impl_pose_filter')
    (evidence/'bit.tcl').write_text(remap((OLD_E/'bit.tcl').read_text()),newline='\n')
    for name in ('call_procise_disable_icap.bat','procise_run_disable_icap.tcl'):
        (work/name).write_text(remap((OLD/name).read_text()),newline='\n')


def prepare(work, lanes):
    work.mkdir(parents=True, exist_ok=False)
    source = work / 'sources'; source.mkdir()
    evidence = work / 'reports'; evidence.mkdir()
    for sub in ('physical', 'pipeline-physical', 'physical-final'):
        (evidence / sub).mkdir()
    text = (BASE / 'sources/ps_ai_peripheral.sv').read_text()
    anchor = "hdmi_cam_router #(.HDMI_BASE(32'h400b0000)) hdmi_router"
    old_upstream = '.upstream(drain_control_passthrough.slave)'
    if text.count(anchor) != 1 or text.count(old_upstream) != 1:
        raise ValueError('Changed GP routing must be inspected')
    text = text.replace(old_upstream, '.upstream(filter_passthrough.slave)', 1)
    block = f'''// Presentation filter only: existing GP 100 MHz, no HP master or new clock.
mna_gp_ww_itf filter_csr(),filter_passthrough();
hdmi_cam_router #(.HDMI_BASE(32'h400b1000),.DECODE_LSB(12)) filter_router(
 .clk(gp_clk),.resetn(~gp_clk_rst),.upstream(drain_control_passthrough.slave),
 .camera(filter_passthrough.master),.hdmi(filter_csr.master));
pose_filter_csr #(.LANES({lanes})) presentation_filter(
 .clk(gp_clk),.resetn(~gp_clk_rst),.wr_valid(filter_csr.awwvalid),.wr_addr(filter_csr.awwaddr[11:0]),
 .wr_data(filter_csr.awwdata),.wr_ready(filter_csr.awwready),.rd_valid(filter_csr.arvalid),
 .rd_addr(filter_csr.araddr[11:0]),.rd_ready(filter_csr.arready),.rsp_valid(filter_csr.rvalid),
 .rsp_data(filter_csr.rdata),.rsp_ready(filter_csr.rready));
'''
    (source / 'ps_ai_peripheral.sv').write_text(text.replace(anchor, block + anchor), newline='\n')
    for path in (HERE/'rtl').glob('pose_filter*.sv'):
        (source/path.name).write_bytes(path.read_bytes())
    # Restrict inherited exceptions to their old logic. Never include new
    # filter registers in legacy clock cuts; no new exception is introduced.
    constraints = ('hdmi_cdc.tcl', 'ps_release_factory_clocks.tcl', 'consumer_capture_scope.tcl')
    for name in constraints:
        value = (BASE / 'sources' / name).read_text()
        value = value.replace('NAME !~ U0_ps_ai_peripheral/startup_drain/*',
          'NAME !~ U0_ps_ai_peripheral/startup_drain/* && NAME !~ U0_ps_ai_peripheral/presentation_filter/*')
        value = value.replace('NAME =~ U0_ps_ai_peripheral/startup_drain/*',
          'NAME =~ U0_ps_ai_peripheral/startup_drain/* || NAME =~ U0_ps_ai_peripheral/presentation_filter/*')
        (source / name).write_text(value, newline='\n')
    def remap(value):
        value = value.replace(OLD.as_posix(), work.as_posix()).replace(OLD_E.as_posix(), evidence.as_posix())
        for name in ('ps_ai_peripheral.sv', *constraints):
            value = value.replace((BASE / 'sources' / name).as_posix(), (source / name).as_posix())
        return value
    for stage in ('synthesis', 'opt', 'place', 'route'):
        value = remap((OLD_E / (stage + '.tcl')).read_text())
        if stage == 'synthesis':
            reads = ''.join('read_verilog -sv {' + (source / n).as_posix() + '}\n'
                            for n in ('pose_filter_lane.sv', 'pose_filter.sv', 'pose_filter_csr.sv'))
            value = value.replace('synth_design -top', reads + 'synth_design -top', 1)
        if stage == 'place':
            old_reference = (ROOT / '.local/hdmi-probe-free-20261025-r1/pipeline-routed.dcp').as_posix()
            value = value.replace(old_reference, (OLD / 'pipeline-scoped.dcp').as_posix())
        if stage == 'opt':
            value = value.replace('opt_design\n', 'source {' + (source / 'consumer_capture_scope.tcl').as_posix() + '}\nopt_design\n')
        (evidence / (stage + '.tcl')).write_text(value, newline='\n')
    report = remap((OLD_E / 'report_final.tcl').read_text()).replace('pipeline-scoped.dcp', 'pipeline-routed.dcp')
    checks = '''
set filter_cells [get_cells -quiet -hier -filter {NAME =~ U0_ps_ai_peripheral/presentation_filter/*}]
if {![llength $filter_cells]} {error "Filter hierarchy missing"}
set filter_regs [filter $filter_cells {IS_SEQUENTIAL == 1}]
set filter_clocks [get_clocks -of_objects [get_pins -of_objects $filter_regs -filter {IS_CLOCK == 1}]]
foreach c $filter_clocks {if {abs([get_property PERIOD $c]-10)>0.001} {error "Filter clock differs from the existing GP source: $c"}}
if {![llength $filter_clocks]} {error "Filter clock missing"}
foreach mode {max min} {
 set p [get_timing_paths -delay_type $mode -to $filter_regs -max_paths 1]
 if {![llength $p] || [get_property SLACK $p]<0} {error "Filter $mode timing failed/missing"}
 puts $f "FILTER_TIMING\\t$mode\\t[get_property SLACK $p]"
}
report_utilization -cells [get_cells U0_ps_ai_peripheral/presentation_filter] -file $out/filter-utilization.rpt
report_utilization -file $out/total-utilization.rpt
report_cdc -details -cells [get_cells U0_ps_ai_peripheral/presentation_filter] -file $out/filter-cdc.rpt
'''
    report = report.replace('close $f', checks + '\nclose $f')
    (evidence / 'report.tcl').write_text(report, newline='\n')
    runner = (BASE / 'run_stage.py').read_text().replace('parents[3]', 'parents[2]')
    runner = runner.replace("ROOT / '.local/hdmi-probe-free-drain-20261026-r1'", 'Path(__file__).resolve().parent')
    runner = runner.replace("ROOT / 'tools/pose-v1/evidence/hdmi-probe-free-drain-20261026-r1'", "WORK / 'reports'")
    (work / 'run_stage.py').write_text(runner, newline='\n')
    manifest = dict(profile='probe-free-drain-filter-v1', lanes=lanes, deployment_qualified=False,
      baseline_BOOT_sha256='651728c52e8db5b2e512990fd28e599872fd1a4306876520ed163449d814a5d4',
      startup_ABI='0x48444302', filter_ABI='0x504f5301', filter_CSR='0x400b1000-0x400b1fff', existing_GP_MHz=100,
      preserved=['bounded startup consumer', 'latest functional admission', 'HDMI ownership/STOP', 'AI four paths', 'HP allocation', 'SDK/model'],
      coverage='Latest profile has no native protocol checker; not equivalent to old r45/compact-guard coverage.',
      budgets=dict(LUT=1500 if lanes == 1 else 4000, FF=1000 if lanes == 1 else 3000,
                   DSP=8 if lanes == 1 else 32, BRAM36=4 if lanes == 1 else 16))
    (work / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    prepare_finish(work)
    return manifest

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work', type=Path, required=True)
    p.add_argument('--lanes', type=int, choices=(1, 4), default=4)
    p.add_argument('--finish-only', action='store_true', help='Prepare checks/bit hooks for an existing build without rerunning EDA')
    a = p.parse_args()
    if a.finish_only:
        prepare_finish(a.work.resolve())
        print('Prepared qualification and bit hooks; no board operation')
    else:
        print(json.dumps(prepare(a.work.resolve(), a.lanes)))
