"""Prepare the three HP2 readiness changes and preserve the generated baseline."""
from pathlib import Path
import json

R=Path(__file__).resolve().parents[3]
REF=R/'.local/hdmi-boot-witness-20261019-r23/reference'
W=R/'.local/hdmi-hp2-ready-20261020-r24'
E=R/'tools/pose-v1/evidence/hdmi-hp2-ready-20261020-r24'


def once(source,before,after):
    if source.count(before)!=1:
        raise ValueError('Expected hardware insertion point is not unique: '+before[:90])
    return source.replace(before,after,1)


def main():
    sources=W/'sources';sources.mkdir(parents=True,exist_ok=True);E.mkdir(parents=True,exist_ok=True)
    changes={}
    # This BD-generated file, including its coupler modules, is the source
    # actually consumed by synthesis. The standalone read_observed export is not.
    name='ps_ai.v';p=REF/'fpai_demo_vivado.srcs/sources_1/bd/ps_ai/synth'/name
    saved=E/'ps_ai-before-r24.v'
    if not saved.exists():saved.write_bytes(p.read_bytes())
    t=saved.read_text()
    t=once(t,'    diagnostic_hp2_resetn);','    diagnostic_hp2_resetn,\n    hp2_domain_ready);')
    t=once(t,'  output diagnostic_hp2_resetn;','  output diagnostic_hp2_resetn;\n  input hp2_domain_ready;')
    t=once(t,"  ps_ai_proc_sys_reset_0_0 proc_sys_reset_1\n       (.aux_reset_in(1'b1),\n        .dcm_locked(1'b1),",
        "  // Keep the original reset IP and synchronization. DDR readiness stays\n"
        "  // low while its clock restarts, so an input reset cannot be lost\n"
        "  // solely because the MIG-derived HP clock stopped during the key.\n"
        "  ps_ai_proc_sys_reset_0_0 proc_sys_reset_1\n       (.aux_reset_in(1'b1),\n        .dcm_locked(hp2_domain_ready),")
    (sources/name).write_bytes(t.encode());changes[str(p)]=str(sources/name)
    name='ps_ai_wrapper.sv';p=REF/'rtl'/name;t=p.read_text()
    t=once(t,'    output diagnostic_hp2_resetn\n);','    output diagnostic_hp2_resetn,\n    input hp2_domain_ready\n);')
    t=once(t,'  .diagnostic_hp2_resetn(diagnostic_hp2_resetn)\n);','  .diagnostic_hp2_resetn(diagnostic_hp2_resetn),\n  .hp2_domain_ready(hp2_domain_ready)\n);')
    (sources/name).write_bytes(t.encode());changes[str(p)]=str(sources/name)
    name='ps_ai_peripheral.sv';p=REF/'rtl'/name;t=p.read_text()
    t=once(t,'    .diagnostic_hp2_resetn(diagnostic_hp2_resetn),','    .diagnostic_hp2_resetn(diagnostic_hp2_resetn),\n    .hp2_domain_ready(ddr3_init_done & ~ddr_ui_rst),')
    (sources/name).write_bytes(t.encode());changes[str(p)]=str(sources/name)
    (E/'source-overlay.json').write_text(json.dumps(dict(replacements=changes,generated_source_backup=str(saved),scope='only HP2 proc_sys_reset_1 readiness; no IP upgrade or model/SDK/frequency change',baseline=str(REF),new_BOOT_authorized=False),indent=2))
    print(json.dumps(dict(overlay_files=3,baseline_backup=str(saved),work=str(W))))


if __name__=='__main__':main()
