"""Post-generation contract/port evidence, without editing vendor products."""
from pathlib import Path
import hashlib, json, re, xml.etree.ElementTree as ET
R = Path(__file__).resolve().parents[3]
E = R / 'tools/pose-v1/evidence/hdmi-ip-generation-20261015-r3'
W = R / '.local/hdmi-ip-generation-20261015-r3/reference'
S = R / 'Docs/26嵌赛开发/fpai_demo_fpga'
ns = {'s': 'http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009'}
def cfg(p):
    return {v.attrib['{' + ns['s'] + '}referenceId']: v.text or '' for v in
            ET.parse(p).findall('.//s:configurableElementValue', ns)}
def snapshot(p):
    d = {}
    for line in p.read_text().splitlines():
        n, k, v = line.split('\t')
        d.setdefault(n, {})[k] = bytes.fromhex(v).decode('utf-8')
    return d
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
gate = json.loads((E / 'bounded-contract-gate.json').read_text())
assert gate['passed']
before = snapshot(E / 'config-before-generation.tsv')
after = snapshot(E / 'config-after-generation.tsv')
errors = []
if before != after:
    errors.append({'error': 'IP properties changed during generation'})
models = []
wrappers = []
for item in gate['XCI_sources']:
    old, new = S / item['original'], W / item['candidate']
    a, b = cfg(old), cfg(new)
    am = {k: v for k, v in a.items() if k.startswith('MODELPARAM_VALUE.')}
    bm = {k: v for k, v in b.items() if k.startswith('MODELPARAM_VALUE.')}
    if am != bm:
        errors.append({'error': 'generated HDL model parameter change', 'IP': old.stem})
    models.append({'IP': old.stem, 'model_parameter_count': len(am), 'equal': am == bm,
                   'generated_XCI': str(new), 'sha256': sha(new)})
    if 'regslice' in old.stem:
        files = list(new.parent.glob('synth/*.v'))
        assert len(files) == 1
        text = files[0].read_text()
        body = text[text.index('module '):]
        ports = re.findall(r'^\s*(input|output)\s*(?:wire\s*)?(\[[^\]]+\])?\s*(\w+)\s*;', body, re.M)
        assert ports
        if any('region' in name or 'user' in name or name == 'aclk2x' for _, _, name in ports):
            errors.append({'error': 'new active REGION/USER/CLK2X wrapper port', 'IP': old.stem})
        if not re.search(r'\.aclk2x\(1\x27B0\)', text):
            errors.append({'error': 'CLK2X not tied inactive', 'IP': old.stem})
        for key, value in am.items():
            if key.split('.', 1)[1] in ('C_FAMILY',):
                continue
            name = key.split('.', 1)[1]
            match = re.search(r'\.' + re.escape(name) + r'\(([^)]+)\)', text)
            if match is None or match.group(1) != value:
                errors.append({'error': 'wrapper model differs from XCI', 'IP': old.stem,
                               'parameter': name, 'expected': value, 'actual': match.group(1) if match else None})
        wrappers.append({'IP': old.stem, 'wrapper': str(files[0]), 'sha256': sha(files[0]),
                         'ports': ports, 'inactive_CLK2X_tied_zero': True})
report = {'parameter_and_port_gate_passed': not errors, 'errors': errors,
          'all_28_original_models': models, 'register_slice_wrapper_checks': wrappers,
          'IP_properties_before_after_generation_equal': before == after,
          'AXI_ID_width_warnings_require_routing_test': True,
          'full_system_signoff': False, 'Procise_signoff': False}
(E / 'post-generation-contract.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'passed': not errors, 'errors': errors}, ensure_ascii=False))
if errors:
    raise SystemExit('Generated contract rejected; stop downstream')
