"""一次导入已实板验证的共享核心；只取链接所需源码与头文件，不改算法。"""
from pathlib import Path
import hashlib, json, re, shutil

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'demo_v1'
SOURCE = ROOT / '.local/shared-resident-source-20261015-r1'
UNITS = ['application_core', 'read_input_bridge', 'input_read_sdk', 'input_read_contract',
         'host_cpu_adapter', 'preprocess', 'host_failure_evidence', 'failure_source_readback',
         'host_stage_observation', 'invocation_evidence', 'producer_count_observation',
         'tensor_identity_observation']

def main():
    manifest = json.loads((SOURCE / 'source-manifest.json').read_text())
    hashes = {k.replace('\\', '/'): v for k, v in manifest['files'].items()}
    pending = [name + '.cpp' for name in UNITS] + ['application_core.hpp', 'sdk_profile.hpp']
    selected = {}
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        source = SOURCE / 'baseline' / name
        raw = source.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != hashes['baseline/' + name]:
            raise ValueError('Frozen source changed: ' + name)
        selected[name] = digest
        pending.extend(re.findall(r'^#include "([^"]+)"', raw.decode(), re.M))
    target = DEST / 'shared_fp16'
    target.mkdir(exist_ok=False)
    for name in selected:
        shutil.copyfile(SOURCE / 'baseline' / name, target / name)
    shutil.copyfile(SOURCE / 'shared_output_gate.hpp', target / 'shared_output_gate.hpp')
    selected['shared_output_gate.hpp'] = hashlib.sha256((target / 'shared_output_gate.hpp').read_bytes()).hexdigest()
    (DEST / 'shared-source.json').write_text(json.dumps({
        'origin': str(SOURCE), 'validated_run': 'shared-stability-20261015-r2',
        'unchanged_math_and_SDK_bridge': True, 'files': selected, 'units': UNITS
    }, indent=2) + '\n')
    print('Imported', len(selected), 'required files')

if __name__ == '__main__':
    main()
