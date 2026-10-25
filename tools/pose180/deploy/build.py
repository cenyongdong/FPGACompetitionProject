"""Compile a separate model-only target, with no legacy Host compute bridge."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import tarfile
import argparse
from convert import ROOT, OUT, save

HERE = Path(__file__).resolve().parent
DOCKER = 'C:/Program Files/Docker/Docker/resources/bin/docker.exe'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--revision',default='r3',choices=('r3',))
    args=parser.parse_args()
    build = ROOT / ('.local/pose180-deploy-20261024-'+args.revision)
    build.mkdir(exist_ok=True)
    if (build/'package.tar').exists():
        raise ValueError('Completed package already exists; preserve it')
    steps = json.loads((build/'steps.json').read_text()) if (build/'steps.json').exists() else []
    def run(*argv):
        result = subprocess.run([DOCKER, *argv], capture_output=True)
        stem = str(len(steps)).zfill(2)
        (build/(stem+'.stdout.log')).write_bytes(result.stdout)
        (build/(stem+'.stderr.log')).write_bytes(result.stderr)
        steps.append(dict(argv=argv,native_exit=result.returncode))
        save(build/'steps.json',steps)
        if result.returncode:
            raise RuntimeError(result.stderr.decode(errors='replace')[-3000:]+result.stdout.decode(errors='replace')[-3000:])
        return result.stdout
    expected = json.loads((ROOT/'.local/shared-stability-delivery-20261015-r2/package.json').read_text())
    native = run('exec','FPAI','sha256sum',*['/usr/lib/aarch64-linux-gnu/'+n for n in expected['libraries']]).decode()
    if {Path(line.split()[1]).name:line.split()[0] for line in native.splitlines()} != expected['libraries']:
        raise ValueError('Actual cross-build SDK differs')
    remote = '/tmp/pose180-deploy-20261024-'+args.revision
    run('exec','FPAI','mkdir','-p',remote)
    for name in ('CMakeLists.txt','main.cpp'):
        run('cp',str(HERE/name),'FPAI:'+remote+'/'+name)
    run('exec','FPAI','cmake','-S',remote,'-B',remote+'/build','-DCMAKE_SYSTEM_NAME=Linux','-DCMAKE_SYSTEM_PROCESSOR=aarch64',
        '-DCMAKE_CXX_COMPILER=aarch64-linux-gnu-g++','-DCMAKE_PREFIX_PATH=/usr/cmake','-DCMAKE_BUILD_TYPE=Release')
    run('exec','FPAI','cmake','--build',remote+'/build','--parallel','2')
    symbols = run('exec','FPAI','aarch64-linux-gnu-nm','-C',remote+'/build/pose180_validate').decode()
    if any(name in symbols for name in ('mixed_candidate','cpu_candidate','source_diagnostic','read_input_bridge','register_ops')):
        raise ValueError('Legacy TopK/Gather Host bridge was linked')
    (build/'symbols.txt').write_text(symbols)
    package = build/'package';package.mkdir()
    run('cp','FPAI:'+remote+'/build/pose180_validate',str(package/'pose180_validate'))
    (package/'models').mkdir();(package/'fixtures').mkdir()
    for name in ('piw24_pose180_ZG.json','piw24_pose180_ZG.raw'):
        shutil.copyfile(OUT/name,package/'models'/name)
    for path in (OUT/'fixtures').glob('*.f32'):
        shutil.copyfile(path,package/'fixtures'/path.name)
    shutil.copyfile(OUT/'fixtures/cases.json',package/'fixtures/cases.json')
    shutil.copyfile(OUT/'reference-generated/approved-first-board-review.json',package/'prior-first-review.json')
    shutil.copyfile(HERE/'numerical-policy-approved.json',package/'numerical-policy.json')
    shutil.copyfile(HERE/'stress-policy.json',package/'stress-policy.json')
    shutil.copyfile(HERE/'board_guard.py',package/'board_guard.py')
    shutil.copyfile(ROOT/'demo_v1/tools/preflight.py',package/'preflight.py')
    identity = dict(expected_boot_files=expected['expected_boot_files'],libraries=expected['libraries'],
                    files={str(p.relative_to(package)).replace('\\','/'):sha(p) for p in package.rglob('*') if p.is_file()},
                    TopK=0,Host_compute=0,legacy_internal_bridge_linked=False,
                    gate='User subsequently approves direct stress ignoring numerical error; preserve all raw outputs/error metrics, stop on nonfinite/SDK/resource failure; original numerical gates and failures retained')
    save(package/'identity.json',identity)
    with tarfile.open(build/'package.tar','w') as archive:
        for path in package.rglob('*'):
            if path.is_file():
                info=archive.gettarinfo(str(path),arcname=path.relative_to(package).as_posix())
                if path.name=='pose180_validate':info.mode=0o755
                with path.open('rb') as source:archive.addfile(info,source)
    save(build/'package-summary.json',dict(package=str(build/'package.tar'),sha256=sha(build/'package.tar'),
                                         legacy_bridge_linked=False,board_executed=False))
    print((build/'package-summary.json').read_text())


if __name__ == '__main__':
    main()
