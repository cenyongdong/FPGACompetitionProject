"""Run the native quantized Host graph; preserve logs and complete outputs."""
import json
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import time

from convert import ROOT, OUT, BIN, NAME, save


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--generated',action='store_true')
    args=parser.parse_args()
    suffix='ZG' if args.generated else 'quantized'
    reference_dir='reference-generated' if args.generated else 'reference'
    graph=json.loads((OUT/(NAME+'_'+suffix+'.json')).read_text())
    ports=next(op['inputs'] for op in graph['ops'] if op['_type_key']=='icraft::xir::Output')
    dump_ids=','.join(str(p['v_id']) for p in ports)
    runtime = json.loads((ROOT / '.local/icraft-runtime/cuda-11.8.0/runtime-manifest.json').read_text())
    paths = [str(BIN)]
    for component in runtime['components']:
        paths.extend(component['bin_dirs'])
    env = dict(os.environ, PATH=';'.join(paths) + ';' + os.environ.get('PATH', ''),
               OMP_NUM_THREADS='2', MKL_NUM_THREADS='2')
    cases = json.loads((OUT / 'fixtures/cases.json').read_text())
    for row in cases:
        name = row['name']
        shutil.copyfile(OUT / 'fixtures' / (name + '.input.f32'), OUT / 'fixtures' / (name + '.input.ftmp'))
        folder = OUT / reference_dir / name
        folder.mkdir(parents=True, exist_ok=False)
        config = folder / 'quantized.toml'
        config.write_text('[run]\njson = "./piw24_pose180_'+suffix+'.json"\nraw = "./piw24_pose180_'+suffix+'.raw"\n'
                          'input = "./fixtures/' + name + '.input.ftmp"\nbackends = "Host"\n'
                          'dump_format = "SFB"\ndump_ftmp = "'+dump_ids+'"\n'
                          'log_path = "./'+reference_dir+'/' + name + '/native"\n', encoding='utf-8')
        argv = [str(BIN / 'icraft.exe'), 'run', str(config)]
        begin = time.monotonic()
        with (folder / 'stdout.log').open('xb') as stdout, (folder / 'stderr.log').open('xb') as stderr:
            child = subprocess.Popen(argv, cwd=OUT, env=env, stdout=stdout, stderr=stderr)
            save(folder / 'invocation.json', dict(argv=argv, pid=child.pid, started=time.time()))
            code = child.wait()
        save(folder / 'exit.json', dict(native_exit=code, seconds=time.monotonic()-begin))
        if code:
            raise RuntimeError(name + ' native quantized Host reference failed: ' + str(code))
        print(json.dumps(dict(case=name, native_exit=code, seconds=time.monotonic()-begin)), flush=True)


if __name__ == '__main__':
    main()
