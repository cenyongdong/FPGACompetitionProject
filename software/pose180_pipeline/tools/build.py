"""Build only changed software; retain native logs and existing FPGA assets."""
from pathlib import Path
import json
import subprocess
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / '.local/pose180-pipeline-20261025-r1'
DOCKER = 'C:/Program Files/Docker/Docker/resources/bin/docker.exe'


def main():
    OUT.mkdir(exist_ok=True)
    steps = json.loads((OUT/'build.json').read_text()) if (OUT/'build.json').exists() else []
    def run(name, *args):
        started = time.monotonic()
        stem=str(len(steps)).zfill(2)+'-'+name
        with (OUT/(stem+'.stdout.log')).open('xb') as stdout, (OUT/(stem+'.stderr.log')).open('xb') as stderr:
            result = subprocess.run([DOCKER, *args], stdout=stdout, stderr=stderr)
        steps.append(dict(stage=name, argv=args, native_exit=result.returncode, seconds=time.monotonic()-started,log_stem=stem))
        (OUT/'build.json').write_text(json.dumps(steps, indent=2)+'\n')
        print(json.dumps(steps[-1]), flush=True)
        if result.returncode:
            raise RuntimeError(name+': '+(OUT/(stem+'.stderr.log')).read_text(errors='replace')[-2200:])
    status = subprocess.check_output([DOCKER, 'inspect', '--format', '{{.State.Status}}', 'FPAI']).strip()
    started_here = status == b'exited'
    if started_here: run('container-start', 'start', 'FPAI')
    try:
        source='/workspace/software/pose180_pipeline'
        native='/workspace/.local/pose180-pipeline-20261025-r1/native'
        arm='/workspace/.local/pose180-pipeline-20261025-r1/arm64'
        run('native-configure','exec','FPAI','cmake','-S',source,'-B',native,'-DCMAKE_BUILD_TYPE=Release')
        run('native-compile','exec','FPAI','cmake','--build',native,'--parallel','2')
        run('buffer-tests','exec','FPAI',native+'/buffer_tests')
        run('renderer-tests','exec','FPAI',native+'/renderer_tests')
        run('arm-configure','exec','FPAI','cmake','-S',source,'-B',arm,
            '-DCMAKE_SYSTEM_NAME=Linux','-DCMAKE_SYSTEM_PROCESSOR=aarch64',
            '-DCMAKE_CXX_COMPILER=aarch64-linux-gnu-g++','-DCMAKE_PREFIX_PATH=/usr/cmake',
            '-DCMAKE_BUILD_TYPE=Release','-DPOSE180_BUILD_SDK=ON')
        run('arm-compile','exec','FPAI','cmake','--build',arm,'--target','pose180_pipeline','--parallel','2')
        symbols=subprocess.check_output([DOCKER,'exec','FPAI','aarch64-linux-gnu-nm','-C',arm+'/pose180_pipeline']).decode()
        if any(name in symbols for name in ('read_input_bridge','input_read_sdk','register_ops','host_cpu_adapter')):
            raise RuntimeError('Legacy internal Host bridge linked')
        (OUT/'symbols.txt').write_text(symbols)
    finally:
        if started_here: run('container-stop','stop','FPAI')


if __name__ == '__main__':
    main()
