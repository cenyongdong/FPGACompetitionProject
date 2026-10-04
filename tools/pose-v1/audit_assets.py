"""Record exact approved model/source/build identities, without executing it."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--repo', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    project = Path(__file__).resolve().parents[2]
    generated = args.repo / 'result/icraft_2024'
    graph_path = generated / 'piw24_ZG.json'
    graph = json.loads(graph_path.read_text(encoding='utf-8'))
    host = [op for op in graph['ops'] if op['compile_target'] == '@hostt']
    source = list((project/'software/pose_v1').rglob('*.cpp')) + list((project/'software/pose_v1').rglob('*.hpp'))
    source += [project/'software/pose_v1/CMakeLists.txt']
    source += list((project/'tools/pose-v1').glob('*.py')) + list((project/'tools/pose-v1').glob('*.ps1'))
    files = [graph_path, generated/'piw24_ZG.raw',
             args.repo/'result/code_faithful/person_in_wifi_2024_best_epoch442_full.onnx',
             args.repo/'opera/datasets/wifi_pose.py',
             project/'.local/pose-v1-build/pose_preprocess_check.arm64', *source]
    report = {'scope':'offline identities only; no inference',
              'model_version':'2024 epoch442 (user-selected)',
              'icraft_version':graph['icraft_version'],'ai_target':graph['ai_target'],
              'params_bytes':graph['params_bytes'],
              'compile_targets':dict(Counter(op['compile_target'] for op in graph['ops'])),
              'host_ops':[{'type':op['_type_key'],'op_id':op['op_id']} for op in host],
              'files':[{'path':str(f),'bytes':f.stat().st_size,'sha256':sha256(f)} for f in files],
              'hardware_baseline_verified':False,'npu_executed':False}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Assets recorded:',len(files),'Host compute ops:',len(host)-2)


if __name__=='__main__':
    main()
