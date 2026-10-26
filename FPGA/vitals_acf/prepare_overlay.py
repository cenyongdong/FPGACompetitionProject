"""Prepare an isolated r45+ACF source overlay, preserving every old protection.

No EDA, BOOT, deployment qualification or device access. This is not the earlier
probe-free/compact-guard overlay and does not claim their resource savings.
"""
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
def prepare(output):
    baseline=ROOT/'FPGA/hdmi_candidate/diagnostics/deferred_consume_r45/sources/ps_ai_peripheral.sv'
    text=baseline.read_text();anchor='mna_gp_ww_itf cycletrace_passthrough(),cycletrace_csr();'
    old='.upstream(cam.slave)'
    if text.count(anchor)!=1 or text.count(old)!=1:raise ValueError('Inspect changed r45 GP entry before generating overlay')
    # Replace the old upstream only. Every old monitor/consumer and address
    # decode remains in the downstream chain, with all original constraints.
    text=text.replace(old,'.upstream(vitals_passthrough.slave)',1)
    insert='''mna_gp_ww_itf vitals_passthrough();
vitals_acf_bridge vitals_acf(.clk(gp_clk),.resetn(~gp_clk_rst),
 .upstream(cam.slave),.downstream(vitals_passthrough.master));
'''
    text=text.replace(anchor,insert+anchor,1)
    output.mkdir(parents=True,exist_ok=False)
    (output/'ps_ai_peripheral.sv').write_text(text,newline='\n')
    manifest=dict(profile='vitals-acf-v1',deployment_qualified=False,baseline=str(baseline),
        source_overlay=str(output/'ps_ai_peripheral.sv'),rtl=[str(HERE/'rtl'/n) for n in ('vitals_acf_csr.sv','vitals_acf_bridge.sv')],
        csr_base='0x400b2000',csr_bytes=256,clock='existing gp_clk 50MHz',
        unchanged=['AI four paths','HP allocation','all r45 diagnostics','startup drain and admission','all existing constraints','pose CPU postprocessing'],
        pending=['full target elaboration/implementation and timing','bit/BOOT identity','bounded actual PS transport and functional validation'],
        resource_scope='381 LUT / 237 FF / 3 BRAM36 / 1 DSP applies to CSR core only; bridge and whole-device packing pending')
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2));return manifest
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(prepare(a.output.resolve()),indent=2))
