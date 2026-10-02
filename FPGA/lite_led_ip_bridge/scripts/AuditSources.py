"""Audit this specific generated xlconcat closure and freeze its file hashes."""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

project = Path(__file__).resolve().parents[1]
generated = project / 'ip/led_state_concat'
vendor = Path('D:/Xilinx/Vivado/2019.1/data/ip/xilinx/xlconcat_v2_1')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def code(p):
    return re.sub(r'//[^\n]*|/\*.*?\*/', '', p.read_text(), flags=re.S)

library = generated / 'hdl/xlconcat_v2_1_vl_rfs.v'
wrapper = generated / 'synth/led_state_concat.v'
rtl = project / 'rtl/lite_led_chaser.v'
require(sha(library) == sha(vendor / 'hdl/xlconcat_v2_1_vl_rfs.v') ==
        'bf101401b966e7c7121bd17b0099f468f8e5fb15a376ac2e747885cdafd86689',
        'Generated library differs from audited installed vendor source')
for path, module in [(library, 'xlconcat_v2_1_3_xlconcat'),
                     (wrapper, 'led_state_concat'), (rtl, 'lite_led_chaser')]:
    source = code(path)
    require(re.findall(r'\bmodule\s+(\w+)', source) == [module],
            f'Unexpected module definitions: {path}')
    require(not re.search(r'`include|\bblack_box\b|\bsyn_black_box\b|\bprotect\b', source, re.I),
            f'Unexpected include/protected/black-box dependency: {path}')
require(re.search(r'xlconcat_v2_1_3_xlconcat\s*#\s*\(', code(wrapper)), 'Missing actual vendor instance')
for name, value in [('NUM_PORTS', 4), ('dout_width', 4)] + [(f'IN{i}_WIDTH', 1) for i in range(4)]:
    require(re.search(rf'\.{name}\({value}\)', code(wrapper)), f'Incorrect wrapper parameter {name}')
require(re.search(r'assign\s+dout\s*=\s*\{\s*In3\s*,\s*In2\s*,\s*In1\s*,\s*In0\s*\}', code(library)),
        'Missing selected vendor generate implementation')
require(re.search(r'led_state_concat\s+state_permutation\s*\(', code(rtl)), 'RTL does not use generated wrapper')
require('led_state <= next_state' in code(rtl), 'IP output not used in LED state update')
require('Vivado 2019.1' in wrapper.read_text() and 'IP Revision: 3' in wrapper.read_text(), 'Wrong generated version')

tree = ET.parse(generated / 'led_state_concat.xci')
ns = {'s': 'http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009'}
parameters = {}
for element in tree.findall('.//s:configurableElementValue', ns):
    parameters[element.attrib.get('{'+ns['s']+'}referenceId', '')] = element.text
for name, value in [('NUM_PORTS', '4'), ('dout_width', '4')] + [(f'IN{i}_WIDTH', '1') for i in range(4)]:
    require(parameters.get('PARAM_VALUE.' + name) == value, f'XCI parameter mismatch: {name}')

entries = []
for path, kind in [(library, 'ip_library'), (wrapper, 'ip_synthesis_wrapper'), (rtl, 'rtl')]:
    entries.append({'path': path.relative_to(project).as_posix(), 'stage_name': path.name,
                    'kind': kind, 'sha256': sha(path), 'size': path.stat().st_size})
manifest = {
    'status': 'specific_plaintext_source_closure_audited',
    'timestamp_utc': datetime.now(timezone.utc).isoformat(),
    'ip': {'vlnv': 'xilinx.com:ip:xlconcat:2.1', 'revision': 3, 'vivado': '2019.1',
           'num_ports': 4, 'input_widths': [1]*4, 'output_width': 4,
           'frontend_metadata_part': 'xc7z030ffg676-2', 'physical_device': 'JFMQL30TAI676H',
           'generate_synth_checkpoint': False, 'vendor_source_unmodified': True},
    'design_sources': entries,
    'xci': {'path': 'ip/led_state_concat/led_state_concat.xci',
            'sha256': sha(generated / 'led_state_concat.xci')},
    'module_closure': ['lite_led_chaser', 'led_state_concat', 'xlconcat_v2_1_3_xlconcat'],
    'catalog_component': {'path': str(vendor / 'component.xml'), 'sha256': sha(vendor / 'component.xml')},
    'xci_parameters': parameters,
    'scope': 'Explicit review for these three modules; not a generic HDL dependency parser or IP compatibility guarantee.'
}
(project / 'source-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
print('SOURCE_AUDIT_PASS', project / 'source-manifest.json')
