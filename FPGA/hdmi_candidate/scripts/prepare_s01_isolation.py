"""Prepare a source-only S01 isolation, preserving the qualified AI/PS topology."""
from pathlib import Path
import hashlib
import json
import re

R = Path(__file__).resolve().parents[3]
B = R / 'FPGA/hdmi_candidate/baselines/ps_release_r26'
OLD = R / '.local/hdmi-ps-release-20261020-r26'
OE = R / 'tools/pose-v1/evidence/hdmi-ps-release-20261020-r26'
W = R / '.local/hdmi-s01-isolation-20261022-r28'
E = R / 'tools/pose-v1/evidence/hdmi-s01-isolation-20261022-r28'
S = W / 'sources'


def block(text, begin, end):
    a = text.index(begin)
    b = text.index(end, a)
    return a, b, text[a:b]


def isolate_peripheral(original, wrapper):
    # Infer the complete source-side input contract from the unchanged wrapper.
    inputs = re.findall(r'^\s*input\s+(?:\[[^\]]+\]\s*)?S_AXI_HP2_1_(\w+)\s*[,\n]',
                        wrapper, re.M)
    if len(inputs) != 27 or len(set(inputs)) != 27:
        raise ValueError('Unexpected factory S01 input contract')
    t = original
    a, b, frame = block(t, 'frame_to_ps_largebuf #', '// Six-boundary passive')
    frame_inputs = {'awready', 'wready', 'bid', 'bresp', 'bvalid'}
    pattern = r'(\.m00_axi_(\w+)\s*\()\s*S_AXI_HP2_\w+\s*(\))'
    frame, n = re.subn(pattern, lambda m: m[1] + ("'0" if m[2] in frame_inputs else '') + m[3], frame)
    if n != 20 or 'S_AXI_HP2_' in frame:
        raise ValueError('Legacy write branch was not fully detached')
    t = t[:a] + frame + t[b:]
    a, b, hdmi = block(t, 'hdmi_board hdmi_display(', 'assign S_AXI_HP2_RDISSUECAP1_EN')
    hdmi_inputs = {'arready', 'rdata', 'rresp', 'rid', 'rlast', 'rvalid'}
    pattern = r'(\.(\w+)\s*\()\s*S_AXI_HP2_\w+\s*(\))'
    hdmi, n = re.subn(pattern, lambda m: m[1] + ("'0" if m[2] in hdmi_inputs else '') + m[3], hdmi)
    if n != 12 or 'S_AXI_HP2_' in hdmi:
        raise ValueError('HDMI read branch was not fully detached')
    t = t[:a] + hdmi + t[b:]
    for suffix in inputs:
        t = re.sub(r'^\s*assign S_AXI_HP2_' + suffix + r'\s*=.*?;[^\n]*\n', '', t, flags=re.M)
    tie = ('// r28 source isolation: retain both xbar slots and observe actual S01 outputs.\n'
           '// No request and no forced consumption of unknown R/B responses.\n')
    tie += ''.join("assign S_AXI_HP2_" + name + " = '0;\n" for name in inputs)
    t = t.replace('// Six-boundary passive', tie + '\n// Six-boundary passive', 1)
    t = t.replace('// Candidate exclusively owns HP2 AR/R. Camera AW/W/B connections above remain.',
                  '// Diagnostic candidate: HDMI/video are detached from all S01 AXI handshakes.')
    # All AI ports, PS integration, soft-reset provider and observer remain exact.
    for begin, end in [('ps_ai_wrapper ps_ai_wrapper_u0 (', 'AI_Mate ZGolo('),
                       ('AI_Mate ZGolo(', '\nendmodule'),
                       ('frame_trans frame_trans_inst0(', 'ps_ai_wrapper ps_ai_wrapper_u0 ('),
                       ('// Six-boundary passive', '// Passive observer:')]:
        if block(t, begin, end)[2] != block(original, begin, end)[2]:
            raise ValueError('Protected AI/reset/observation integration changed: ' + begin)
    return t, inputs


def remap(text):
    text = text.replace(OE.as_posix(), E.as_posix())
    text = text.replace((OLD/'sources/ps_ai_peripheral.sv').as_posix(), (S/'ps_ai_peripheral.sv').as_posix())
    text = text.replace((OLD/'sources').as_posix(), (B/'sources').as_posix())
    text = text.replace(OLD.as_posix(), W.as_posix())
    # The already qualified factory PS export is reused, not rebuilt or copied.
    text = text.replace((W/'ps-export.dcp').as_posix(), (OLD/'ps-export.dcp').as_posix())
    return text


def isolated_hdmi_cdc(text):
    """Keep all surviving CDC checks; prove folded FIFO inputs are constants."""
    old='''  set src [hdmi_cdc_cells $source $expected]
  set dst [hdmi_cdc_cells $target $expected]'''
    new='''  set src [hdmi_cdc_cells $source 0]
  set dst [hdmi_cdc_cells $target 0]
  if {![llength $src]} {
   if {![string match scanout/fifo/* $source]} {error "Unexpected removed Gray source $source"}
   foreach pin [hdmi_cdc_pins $dst D] {
    set drivers [get_cells -of_objects [get_pins -leaf -of_objects [get_nets -segments -of_objects $pin] -filter {DIRECTION == OUT}]]
    if {[lsort -unique [get_property REF_NAME $drivers]] ni {GND VCC}} {error "Unbounded surviving FIFO input $pin"}
   }
   puts "ISOLATED_FIFO_CONSTANT_CDC $source destination_bits=[llength $dst]"
   return
  }'''
    if old not in text:raise ValueError('Factory HDMI Gray check changed')
    text=text.replace(old,new,1)
    text=text.replace('  set c [hdmi_cdc_cells $path 1]',
        '  set c [hdmi_cdc_cells $path 0]\n  if {![llength $c]} {puts "ISOLATED_REMOVED_SYNC $path";continue}',1)
    text=text.replace('  set cells [hdmi_cdc_cells $path 3]',
        '  set cells [hdmi_cdc_cells $path 0]\n  if {![llength $cells] && [string match scanout/fifo/* $path]} {puts "ISOLATED_REMOVED_FIFO_RESET $path";continue}',1)
    return text


def isolated_read_monitor_cdc(text):
    # The inactive S01 first-error word becomes zero. Vivado can leave zero-D
    # capture flops before opt_design while eliminating the matching source.
    marker='set ai_read_capture_indices [ai_read_mon_indices $ai_read_capture]'
    prefix=r'''set isolated_dynamic_capture {}
foreach c $ai_read_capture {
 regexp {\[([0-9]+)\]$} [get_property NAME $c] unused index
 if {[lsearch -exact $ai_read_source_indices $index]<0} {
  set p [get_pins -of_objects $c -filter {REF_PIN_NAME == D}]
  set drivers [get_cells -of_objects [get_pins -leaf -of_objects [get_nets -segments -of_objects $p] -filter {DIRECTION == OUT}]]
  if {[lsort -unique [get_property REF_NAME $drivers]] ne "GND"} {error "Unmatched nonconstant snapshot input $index"}
  puts "ISOLATED_ZERO_CAPTURE_ONLY $index"
 } else {lappend isolated_dynamic_capture $c}
}
set ai_read_capture $isolated_dynamic_capture
'''
    if marker not in text:raise ValueError('Snapshot index gate changed')
    return text.replace(marker,prefix+marker,1)


def main():
    if (W/'synth.dcp').exists() or list(E.glob('*-process.json')):
        raise RuntimeError('This package has already entered native execution')
    S.mkdir(parents=True, exist_ok=True)
    E.mkdir(parents=True, exist_ok=True)
    (E/'qualified-r8').mkdir(exist_ok=True)
    original = (B/'sources/ps_ai_peripheral.sv').read_text()
    peripheral, inputs = isolate_peripheral(original, (B/'sources/ps_ai_wrapper.sv').read_text())
    (S/'ps_ai_peripheral.sv').write_text(peripheral, newline='\n')
    # Constant source inputs have no timing path. All remaining dynamic paths
    # retain the exact old 5 ns/10 ns bounds; no false-path is introduced.
    for name in ('ps_release_cdc.tcl', 'ps_release_raw_flags_cdc.tcl'):
        t = (R/'FPGA/hdmi_candidate/constraints'/name).read_text()
        t = t.replace(r'_reg\[7\]$', r'_reg\[(7|10|12|13)\]$')
        (S/name).write_text(t, newline='\n')
    t = remap((B/'sources/pre-opt.tcl').read_text())
    hdmi=R/'.local/hdmi-boot-witness-20261019-r23/reference/constrs_1/hdmi_cdc.tcl'
    (S/'hdmi_cdc.tcl').write_text(isolated_hdmi_cdc(hdmi.read_text()),newline='\n')
    t=t.replace(hdmi.as_posix(),(S/'hdmi_cdc.tcl').as_posix())
    read_cdc=hdmi.with_name('ai_read_monitor_cdc.tcl')
    (S/'ai_read_monitor_cdc.tcl').write_text(isolated_read_monitor_cdc(read_cdc.read_text()),newline='\n')
    t=t.replace(read_cdc.as_posix(),(S/'ai_read_monitor_cdc.tcl').as_posix())
    for name in ('ps_release_cdc.tcl', 'ps_release_raw_flags_cdc.tcl'):
        t = t.replace((R/'FPGA/hdmi_candidate/constraints'/name).as_posix(), (S/name).as_posix())
    (S/'pre-opt.tcl').write_text(t, newline='\n')
    syn = remap((B/'native/synthesis-r3.tcl').read_text())
    syn = syn.replace('synth-r3.dcp', 'synth.dcp')
    (E/'synthesis.tcl').write_text(syn, newline='\n')
    opt = remap((OE/'opt-r8.tcl').read_text())
    opt = opt.replace('synth-r3.dcp', 'synth.dcp')
    opt = opt.replace((B/'sources/pre-opt.tcl').as_posix(), (S/'pre-opt.tcl').as_posix())
    gate = '''set x U0_ps_ai_peripheral/ps_ai_wrapper_u0/ps_ai_i/axi_interconnect_4
set f [open {@@OUT@@/source-isolation-native.tsv} w]
foreach field {@@FIELDS@@} {
 set p [get_pins -quiet $x/S01_AXI_[string tolower $field]*]
 if {![llength $p]} {error "Missing actual S01 input $field"}
 set n [get_nets -segments -of_objects $p]
 set d [get_pins -leaf -of_objects $n -filter {DIRECTION == OUT}]
 set c [get_cells -of_objects $d]
 set refs [lsort -unique [get_property REF_NAME $c]]
 puts $f "S01_ZERO\\t$field\\t$refs"
 if {$refs ne "GND"} {error "Actual S01 input is not zero: $field $refs"}
}
close $f
'''.replace('@@OUT@@', E.as_posix()).replace('@@FIELDS@@', ' '.join(inputs))
    opt = opt.replace('source {' + (S/'pre-opt.tcl').as_posix() + '}', gate + 'source {' + (S/'pre-opt.tcl').as_posix() + '}', 1)
    (E/'opt.tcl').write_text(opt, newline='\n')
    route = remap((B/'native/route-r8.tcl').read_text())
    route = route.replace('read_checkpoint -incremental {' + (R/'.local/hdmi-boot-witness-20261019-r23/reference/fpai_demo_vivado.runs/impl_hp2ready_r24/ai7030_edif_top_routed.dcp').as_posix() + '}',
                          'read_checkpoint -incremental {' + (OLD/'qualified-routed.dcp').as_posix() + '}')
    (E/'route.tcl').write_text(route, newline='\n')
    final = remap((B/'native/final.tcl').read_text())
    final = final.replace(r'_reg\[7\]$', r'_reg\[(7|10|12|13)\]$')
    final = final.replace('[llength $src]!=374 || [llength $dst]!=374',
                          '![llength $src] || [llength $src]!=[llength $dst]')
    (E/'final.tcl').write_text(final, newline='\n')
    bit = remap((B/'native/bit-r2.tcl').read_text()).replace('impl_ps_release_r26', 'impl_s01_isolation_r28')
    bit = bit.replace('[llength $boot_source]!=374 || [llength $boot_capture]!=374',
                      '![llength $boot_source] || [llength $boot_source]!=[llength $boot_capture]')
    (E/'bit-r2.tcl').write_text(bit, newline='\n')
    overlay = {'replacements': {str(B/'sources'/n): str(S/n if n=='ps_ai_peripheral.sv' else B/'sources'/n)
                               for n in ('ps_ai.v','ps_ai_wrapper.sv','ps_ai_peripheral.sv','ai_read_monitor.sv')},
               'scope':'S01 source isolation only; unchanged AI four-HC/PS/xbar/reset integration',
               'S01_inputs_held_zero':inputs,'source_isolation_not_xbar_removal':True}
    (E/'source-overlay.json').write_text(json.dumps(overlay, indent=2)+'\n')
    state = {'status':'source_prepared_not_built','baseline_tag':'codex/hdmi-before-s01-isolation-20261022',
             'authorization':'User approved HDMI/legacy video branch isolation on 2026-10-22, after Git baseline and standalone Markdown report.',
             'budget':{'candidate_starts_max':1,'original_fallbacks_max':1,'SDK_Open_max':0},
             'actual_candidate_starts':0,'actual_original_fallbacks':0,'actual_SDK_Open':0,
             'DMA':False,'inference':False,'HDMI_START':False,'HDMI_long_term':False,'physical_keys':0,
             'PS_firmware_or_register_changes':False,'HP_port_reallocation':False,'old_DATA':'independently paused',
             'old_r26':'closed; no balance reused','board_access_this_package':False,'background_tasks':[],
             'next':'Native synth/link prove all S01 source inputs zero; complete timing/CDC/DRC and bit/BOOT qualification before board actions.'}
    (E/'state.json').write_text(json.dumps(state, indent=2)+'\n')
    print(json.dumps({'S01_inputs_zero':len(inputs),'protected_AI_reset_blocks_identical':True,'work':str(W)}))


if __name__ == '__main__':
    main()
