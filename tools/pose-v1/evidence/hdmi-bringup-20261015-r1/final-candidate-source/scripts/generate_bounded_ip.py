"""Approved finite IP exceptions; fresh copy, gate before target generation.
Original rejected gates remain immutable. No hooks, synthesis, board or BOOT writes.
"""
from pathlib import Path
import hashlib, json, os, shutil, subprocess, sys, time, xml.etree.ElementTree as ET

R = Path(__file__).resolve().parents[3]
OLD = R / '.local/hdmi-bd-validation-20261015-r1/reference'
BASE = R / 'Docs/26嵌赛开发/fpai_demo_fpga'
EV = R / 'tools/pose-v1/evidence'
PRE = EV / 'hdmi-bd-validation-20261015-r1'
revision = sys.argv[1] if len(sys.argv) > 1 else 'r1'
assert revision in ('r1', 'r2', 'r3')
W = R / ('.local/hdmi-ip-generation-20261015-' + revision)
E = EV / W.name
W.mkdir(exist_ok=False)
E.mkdir(exist_ok=False)
ref = W / 'reference'
shutil.copytree(OLD, ref)

def save(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def manifest(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in root.rglob('*') if p.is_file()}

def tp(p):
    return '{' + p.as_posix() + '}'

save(E / 'copied-input-manifest.json', manifest(ref))
save(E / 'authorization.json', {
    'user_reply': '批准有限例外并继续生成验证',
    'plan': 'FPGA/hdmi_candidate/IP-CONTRACT-REVIEW.md',
    'plan_sha256': sha(R / 'FPGA/hdmi_candidate/IP-CONTRACT-REVIEW.md'),
    'old_rejected_gates_preserved': True, 'no_board_operation': True,
    'no_global_patch_hooks': True, 'no_synthesis': True,
    'validation_budget_seconds': 180, 'generation_budget_seconds': 300,
    'generation_stop': 'first error, timeout, locked IP or unknown contract difference',
})
ips = []
for f in ET.parse(ref / 'fpai_demo_vivado.xpr').findall('.//FileSet[@Name="sources_1"]/File'):
    p = Path(f.attrib['Path'].replace('$PPRDIR', ref.as_posix()).replace(
        '$PSRCDIR', (ref / 'fpai_demo_vivado.srcs').as_posix()))
    if p.suffix == '.xci':
        ips.append(p)
assert len(ips) == 13
bd = ref / 'fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ps_ai.bd'
project = W / 'project'
helper = (EV / 'hdmi-ip-revision-20261015-r1/upgrade.tcl').read_text()
helper = helper[helper.index('proc dump_ips'):helper.index('if {[catch')]

def run(stage, body, budget):
    tcl = 'set out [file normalize ' + tp(E) + ']\n' + helper
    tcl += 'if {[catch {\n' + body + '\n} result]} {puts "STAGE_FAIL $result";exit 1}\nexit\n'
    source = W / (stage + '.tcl')
    source.write_text(tcl, encoding='ascii')
    shutil.copyfile(source, E / source.name)
    env = os.environ.copy()
    env['PROCESSOR_ARCHITECTURE'] = 'AMD64'
    args = ['D:/Xilinx/Vivado/2019.1/bin/vivado.bat', '-mode', 'batch', '-nojournal',
            '-log', str(E / (stage + '.log')), '-source', str(source)]
    start = time.monotonic()
    timed_out = False
    with (E / (stage + '.stdout.txt')).open('wb') as out, (E / (stage + '.stderr.txt')).open('wb') as err:
        p = subprocess.Popen(args, cwd=W, env=env, stdout=out, stderr=err,
                             creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            code = p.wait(timeout=budget)
        except subprocess.TimeoutExpired:
            timed_out = True
            k = subprocess.run(['taskkill', '/PID', str(p.pid), '/T', '/F'], capture_output=True, timeout=15)
            (E / (stage + '.cleanup.txt')).write_bytes(k.stdout + k.stderr)
            code = p.wait(timeout=15)
    result = {'exit': code, 'timed_out': timed_out, 'seconds': time.monotonic() - start, 'budget': budget}
    save(E / (stage + '.execution.json'), result)
    print(stage, json.dumps(result), flush=True)
    if code or timed_out:
        print((E / (stage + '.stdout.txt')).read_text(errors='replace')[-4500:], flush=True)
        raise SystemExit('Stage failed; no retry or subsequent stage')

run('validate', '''
create_project hdmi_bounded PROJECTDIR -part xc7z030ffg676-2
set_property ip_repo_paths [list REPO] [current_project]
set_property ip_cache_permissions {} [current_project]
update_ip_catalog
foreach ip [list IPFILES] {read_ip $ip}
add_files -norecurse BDFILE
open_bd_design BDFILE
set port [get_bd_ports gp_axi_aclk]
set association [get_property CONFIG.ASSOCIATED_BUSIF $port]
set kept {}
set removed {}
foreach name [split $association :] {
 if {$name=="gp0_monitor" || $name=="gp1_monitor"} {
  if {[llength [get_bd_intf_ports -quiet $name]]!=0} {error "Monitor interface exists $name"}
  lappend removed $name
 } else {lappend kept $name}
}
if {[lsort $removed] != [list gp0_monitor gp1_monitor]} {error "Unexpected removed association list $removed"}
puts "CLOCK_ASSOCIATION_BEFORE $association"
puts "CLOCK_ASSOCIATION_AFTER [join $kept :]"
set_property CONFIG.ASSOCIATED_BUSIF [join $kept :] $port
puts "VALIDATE_AFTER_ASSOCIATION_CORRECTION_BEGIN"
validate_bd_design
save_bd_design
file copy BDFILE [file join $out bd-validated.json]
dump_ips [file join $out config-validated.tsv]
report_ip_status -file [file join $out IP-status.rpt]
close_project
puts "BOUNDED_VALIDATION_COMPLETE"
'''.replace('PROJECTDIR', tp(project)).replace('REPO', tp(ref / 'PS_AI IP')).replace(
    'IPFILES', ' '.join(tp(p) for p in ips)).replace('BDFILE', tp(bd)), 180)

ns = {'s': 'http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009'}
def cfg(p):
    return {v.attrib['{' + ns['s'] + '}referenceId']: v.text or '' for v in
            ET.parse(p).findall('.//s:configurableElementValue', ns)}

review = json.loads((PRE / 'HDL-and-bus-contract-review.json').read_text(encoding='utf-8'))
approved_roles = json.loads((PRE / 'post-validation-config-gate.json').read_text())['derived_role_renames']
newbd = json.loads((E / 'bd-validated.json').read_text())['design']
oldbd = json.loads((PRE / 'bd-validated.json').read_text())['design']
def at_role(design, role):
    for name in role.strip('/').split('/'):
        design = design['components'][name]
    return design
# Fresh BD validation can choose fresh suffixes for the same managed role.
# Only these five authorized roles may rename; all other BD content stays strict.
renames = {}
for item in approved_roles:
    current_name = at_role(newbd, item['role'])['xci_name']
    renames[item['before']] = current_name
    at_role(oldbd, item['role'])['xci_name'] = current_name
allowed = {}
for key in ('active_bus_interface_differences', 'existing_PARAMETER_differences', 'disabled_CLK2X_metadata_differences'):
    for item in review[key]:
        value = renames[item['IP']] if item['key'] == 'PARAM_VALUE.Component_Name' else item['after']
        allowed[(item['IP'], item['key'])] = (item['before'], value)
added = {item['IP']: item['new_keys'] for item in review['added_parameters_and_bus_metadata']}
assert len(allowed) == 15 and len(renames) == 5 and len(added) == 4
errors = []
accepted = []
used = []
for old in BASE.rglob('*.xci'):
    name = old.stem
    newname = renames.get(name, name)
    candidates = list(ref.rglob(newname + '.xci'))
    if len(candidates) != 1:
        errors.append({'IP': name, 'error': 'missing or duplicate XCI'})
        continue
    new = candidates[0]
    a, b = cfg(old), cfg(new)
    for key, value in a.items():
        if not key.startswith(('MODELPARAM_VALUE.', 'PARAM_VALUE.', 'BUSIFPARAM_VALUE.')):
            continue
        if b.get(key) != value:
            item = {'IP': name, 'key': key, 'before': value, 'after': b.get(key)}
            if allowed.get((name, key)) == (value, b.get(key)):
                accepted.append(item)
            else:
                errors.append(item)
    actual_added = {k: v for k, v in b.items() if k not in a and k.startswith(
        ('MODELPARAM_VALUE.', 'PARAM_VALUE.', 'BUSIFPARAM_VALUE.'))}
    if actual_added != added.get(name, {}):
        errors.append({'IP': name, 'error': 'unexpected added parameter set', 'actual': actual_added})
    used.append({'original': old.relative_to(BASE).as_posix(), 'candidate': new.relative_to(ref).as_posix(),
                 'before_sha256': sha(old), 'after_sha256': sha(new)})
if len(used) != 28:
    errors.append({'error': 'active original XCI count differs', 'count': len(used)})
if len(accepted) != len(allowed):
    errors.append({'error': 'finite exception set differs', 'actual_count': len(accepted)})
# Resolve the allowed missing reset polarity through the actual vendor component.
component = Path('D:/Xilinx/Vivado/2019.1/data/ip/xilinx/axi_register_slice_v2_1/component.xml')
assert sha(component) == review['CLK2X_enablement_primary_source']['sha256']
tree = ET.parse(component)
rst = [v for v in tree.findall('.//s:busInterface', ns) if v.findtext('s:name', namespaces=ns) == 'RST']
assert len(rst) == 1
polarity = [v.findtext('s:value', namespaces=ns) for v in rst[0].findall('s:parameters/s:parameter', ns)
            if v.findtext('s:name', namespaces=ns) == 'POLARITY']
assert polarity == ['ACTIVE_LOW']
# Compare complete BD against successfully propagated version; allow only two stale links removed.
assoc = oldbd['ports']['gp_axi_aclk']['parameters']['ASSOCIATED_BUSIF']['value']
oldbd['ports']['gp_axi_aclk']['parameters']['ASSOCIATED_BUSIF']['value'] = ':'.join(
    v for v in assoc.split(':') if v not in ('gp0_monitor', 'gp1_monitor'))
def canonical(value, key=''):
    if isinstance(value, dict):
        return {k: canonical(v, k) for k, v in value.items() if k not in ('design_info',)}
    if isinstance(value, list):
        result = [canonical(v) for v in value]
        return sorted(result) if all(isinstance(v, str) for v in result) else result
    return value
if canonical(oldbd) != canonical(newbd):
    errors.append({'error': 'BD differs beyond exactly two approved stale associations'})
props = {}
for line in (E / 'config-validated.tsv').read_text().splitlines():
    n, k, v = line.split('\t')
    props.setdefault(n, {})[k] = bytes.fromhex(v).decode('utf-8')
if len(props) != 28 or any(v.get('IS_LOCKED') != '0' for v in props.values()):
    errors.append({'error': 'locked IP or changed IP count'})
validation_log = (E / 'validate.stdout.txt').read_text(errors='replace')
validation_phase = validation_log.split('\nVALIDATE_AFTER_ASSOCIATION_CORRECTION_BEGIN\n')
if len(validation_phase) != 2 or 'BD 41-1287' in validation_phase[-1]:
    errors.append({'error': 'stale bus association warning remains'})
for old in BASE.rglob('*'):
    if old.is_file() and (old.suffix.lower() == '.edif' or 'PS_AI IP' in old.parts):
        new = ref / old.relative_to(BASE)
        if not new.is_file() or sha(old) != sha(new):
            errors.append({'error': 'protected PS package/EDIF changed', 'path': str(old)})
gate = {'passed': not errors, 'errors': errors, 'accepted_exact_exceptions': accepted,
        'approved_added_fields': added, 'managed_role_names': renames,
        'XCI_sources': used, 'original_instances': len(used),
        'original_MODELPARAM_differences': 0 if not errors else 'inspect errors',
        'reset_default': polarity[0], 'generation_has_not_started': True,
        'old_rejected_gates_preserved': True}
save(E / 'bounded-contract-gate.json', gate)
print('bounded gate', json.dumps({'passed': gate['passed'], 'errors': errors}), flush=True)
if errors:
    raise SystemExit('Bounded contract gate rejected; no target generation')
save(E / 'before-generation-manifest.json', manifest(ref))
run('generate', '''
open_project XPR
open_bd_design BDFILE
dump_ips [file join $out config-before-generation.tsv]
puts "TARGET_GENERATION_BEGIN"
foreach path [list IPFILES] {
 puts "GENERATE_STANDALONE $path"
 generate_target all [get_files $path]
}
puts "GENERATE_BD_SYSTEM"
generate_target all [get_files BDFILE]
dump_ips [file join $out config-after-generation.tsv]
report_ip_status -file [file join $out IP-status-after-generation.rpt]
set files [get_files -compile_order sources -used_in synthesis]
set f [open [file join $out synthesis-files.txt] w]
foreach path $files {puts $f $path}
close $f
save_project_as hdmi_generated GENERATED_PROJECT
close_project
puts "BOUNDED_TARGET_GENERATION_COMPLETE"
'''.replace('XPR', tp(project / 'hdmi_bounded.xpr')).replace('BDFILE', tp(bd)).replace(
    'IPFILES', ' '.join(tp(p) for p in ips)).replace('GENERATED_PROJECT', tp(W / 'generated-project')), 300)
save(E / 'generated-manifest.json', manifest(ref))
print('Generated products retained in', ref, flush=True)
