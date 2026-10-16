"""Static contract and format review; never edits or decodes vendor databases."""
from pathlib import Path
import hashlib, json, re, shutil

R = Path(__file__).resolve().parents[3]
E = R / 'tools/pose-v1/evidence/hdmi-jfm-compatibility-20261015-r1'
V = R / 'tools/pose-v1/evidence/hdmi-vivado2019-library-20261015-r1'
patch = R / 'Docs/26嵌赛开发/JFM_Kits/JFM_Kits/ip_patch/030ai'

def sha(p):
 h = hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda: f.read(8 * 1024 * 1024), b''):
   h.update(b)
 return h.hexdigest()

def liberty_ps7(path):
 t = path.read_text(encoding='ascii')
 m = re.search(r'(?m)^cell\(PS7\)\s*\{', t)
 assert m, str(path)
 following = re.search(r'(?m)^cell\(', t[m.end():])
 cell = t[m.start():m.end() + following.start()] if following else t[m.start():]
 pins = re.findall(r'\bpin\(([^)]+)\)\s*\{\s*direction\s*:\s*(\w+)', cell)
 assert len(pins) == len(set(n for n, _ in pins)), 'duplicate Liberty pins'
 return dict(pins)

vendor = liberty_ps7(patch / 'zynq.lib')
installed = liberty_ps7(Path('D:/Xilinx/Vivado/2019.1/data/parts/xilinx/zynq/devint/zynq.lib'))
raw = (V / 'builtin-PS7-pins.txt').read_text(encoding='utf-8')
queried = dict((n.split('/')[-1], {'bidir':'inout'}.get(d.lower(), d.lower())) for n, d in
               (line.split('|') for line in raw.splitlines() if not line.startswith('CELL|')))
assert installed == queried, 'runtime and installed Liberty contract differ'
calls = json.loads((R / 'tools/pose-v1/evidence/hdmi-jfm-pin-review-20261015-r1/PS7-callsite-review.json').read_text())
ai_called = {n for n in calls['terminals'] if n.startswith('AI_')}
missing = sorted(ai_called - queried.keys())
vendor_missing = sorted(ai_called - vendor.keys())
formats = []
pairs = json.loads((R / 'tools/pose-v1/evidence/hdmi-jfm-pin-review-20261015-r1/replacement-review.json').read_text(encoding='utf-8'))['replacement_pairs']
for pair in pairs:
 p = Path(pair['patch']['path'])
 b = p.read_bytes()
 formats.append({'path':str(p),'bytes':len(b),'sha256':sha(p),
                 'header_ascii':b[:24].decode('ascii',errors='replace'),
                 'Xlx_protected_header':b.startswith(b'Xlx'),
                 'contains_NUL_first_8192':b'\0' in b[:8192]})
review = {'date':'2026-10-15','user_confirmed_all_official_material_local_no_2019_1_package':True,
 'latest_scope':'assess migration to 2019.1 first; download 2018.3 only if unavailable',
 'installed_PS7_scalar_pins':len(installed),'runtime_PS7_scalar_pins':len(queried),
 'runtime_matches_installed_Liberty':True,'vendor_PS7_scalar_pins':len(vendor),
 'called_AI_named_terminals':len(ai_called),'called_AI_missing_in_runtime':len(missing),
 'called_AI_missing_in_vendor_Liberty':len(vendor_missing),
 'missing_AI_runtime':missing,'missing_AI_vendor_Liberty':vendor_missing,
 'vendor_runtime_same_named_pin_direction_mismatches':[
  {'pin':n,'vendor':vendor[n],'runtime':queried[n]} for n in sorted(vendor.keys() & queried.keys()) if vendor[n] != queried[n]],
 'format_review':formats,'vendor_database_modified_or_decoded':False,
 'migration_pass':False,'theoretical_impossibility_claimed':False,
 'decision':'No verified local full-system 2019.1 migration path: portable RTL/IP already works; protected primitive/device databases and Procise AI binding remain unsupported. Use version-matched 2018.3 frontend as fallback, subject to independent Procise gate.',
 'references':{'metadata_query':'../hdmi-vivado2019-library-20261015-r1/execution.json',
               'prior_project_local_PS_failure':'../hdmi-jfm-ps-elaboration-20261015-r1/execution.json',
               'native_PS_failure':'../hdmi-native-ps-20261015-r1/execution.json'}}
(E / 'migration-contract-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
archive = R / 'Docs/26嵌赛开发/JFM_Kits.zip'
(E / 'local-kit-archive-identity.json').write_text(json.dumps({'path':str(archive),
 'bytes':archive.stat().st_size,'sha256':sha(archive)},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for name, data in [('vendor-PS7-pins.json',vendor),('runtime-PS7-pins.json',queried)]:
 (E / name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:review[k] for k in ['runtime_PS7_scalar_pins','vendor_PS7_scalar_pins','called_AI_named_terminals','called_AI_missing_in_runtime','called_AI_missing_in_vendor_Liberty','migration_pass']}))
