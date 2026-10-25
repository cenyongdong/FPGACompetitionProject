"""Convert the delivered epoch99 graph with the installed Icraft 3.39 stack."""
import collections
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'model/piw24_pose180_shared-20261024-r1'
BIN = Path('C:/Icraft/CLI v3.39.0/bin')
NAME = 'piw24_pose180'


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def review(stage, suffix):
    graph_path = OUT / (NAME + '_' + suffix + '.json')
    raw_path = OUT / (NAME + '_' + suffix + '.raw')
    graph = json.loads(graph_path.read_text(encoding='utf-8'))
    if graph['ai_target'] != '@zhuget(330)' or graph['icraft_version'] != 'v3.39.0':
        raise ValueError('Actual target or tool version differs')
    if graph['params_bytes'] != raw_path.stat().st_size:
        raise ValueError('Parameter size differs')
    if hashlib.md5(raw_path.read_bytes()).hexdigest() != graph['params_md5']:
        raise ValueError('Native JSON/RAW pair differs')
    counts = collections.Counter(op['_type_key'] for op in graph['ops'])
    forbidden = {k: v for k, v in counts.items() if any(n in k.lower() for n in ('topk', 'gatherelements', 'scatternd'))}
    if forbidden:
        raise ValueError('Candidate-selection operation remains: ' + repr(forbidden))
    inputs = [op for op in graph['ops'] if op['_type_key'] == 'icraft::xir::Input']
    outputs = [op for op in graph['ops'] if op['_type_key'] == 'icraft::xir::Output']
    if len(inputs) != 1 or len(outputs) != 1:
        raise ValueError('Graph port count differs')
    ports = inputs[0]['outputs'] + outputs[0]['inputs']
    if [p['dtype']['shape'] for p in ports] != [[1, 180, 60], [1, 180], [1, 180, 14, 3]]:
        raise ValueError('180-query port shape differs')
    if any(p['dtype']['element_dtype'] != '@fp(32)' for p in ports):
        raise ValueError('Public ports must remain FP32')
    host = [dict(id=op['op_id'], type=op['_type_key']) for op in graph['ops']
            if op['compile_target'] == '@hostt' and op['_type_key'] not in ('icraft::xir::Input', 'icraft::xir::Output')]
    result = dict(stage=stage, operators=dict(counts), host_compute=host,
                  topk=0, candidate_gather_elements=0, scatter_nd=0,
                  port_shapes=[p['dtype']['shape'] for p in ports],
                  raw_bytes=raw_path.stat().st_size,
                  static_layer_count_sum=sum(op.get('layer_count', 0) for op in graph['ops']))
    save(OUT / 'logs' / (stage + '.graph.json'), result)
    return result


def main():
    runtime = json.loads((ROOT / '.local/icraft-runtime/cuda-11.8.0/runtime-manifest.json').read_text())
    if runtime['icraft_version'] != '3.39.0':
        raise ValueError('Runtime version differs')
    search = [str(BIN)]
    for component in runtime['components']:
        search.extend(component['bin_dirs'])
        if any(not Path(item['path']).is_file() for item in component['dlls']):
            raise ValueError('Installed runtime DLL is unavailable')
    env = dict(os.environ, PATH=';'.join(search) + ';' + os.environ.get('PATH', ''))
    records = []
    begin = time.monotonic()
    for stage, suffix in [('parse', 'parsed'), ('optimize', 'optimized'), ('quantize', 'quantized'), ('adapt', 'adapted'), ('generate', 'ZG')]:
        log = OUT / 'logs'
        argv = [str(BIN / 'icraft.exe'), stage, NAME + '.toml']
        with (log / (stage + '.stdout.log')).open('xb') as stdout, (log / (stage + '.stderr.log')).open('xb') as stderr:
            child = subprocess.Popen(argv, cwd=OUT, env=env, stdout=stdout, stderr=stderr)
            save(OUT / 'state.json', dict(stage=stage, status='running', pid=child.pid, command=argv, started=time.time()))
            # Outer tool waits may yield; they never kill the native conversion.
            code = child.wait()
        record = dict(stage=stage, native_exit=code)
        save(log / (stage + '.exit.json'), record)
        if code:
            raise RuntimeError(stage + ' native exit ' + str(code))
        record['graph'] = review(stage, suffix)
        records.append(record)
        print(json.dumps(dict(stage=stage, native_exit=code, graph=record['graph'])), flush=True)
    save(OUT / 'conversion.json', dict(stages=records, seconds=time.monotonic()-begin,
                                      passed=True, board_tested=False))
    save(OUT / 'state.json', dict(status='converted', passed=True, finished=time.time()))


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        save(OUT / 'failure.json', dict(error=repr(error), automatic_retry=False))
        raise
