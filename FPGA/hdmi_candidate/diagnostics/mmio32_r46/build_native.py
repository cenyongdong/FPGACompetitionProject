"""Offline existing-toolchain build; no SDK or board operations."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parent
BUILD=ROOT/'build'
PACKAGE=ROOT/'package'
CONTAINER='FPAI'
REMOTE='/tmp/hp2-mmio32-20261024-r46'
records=[]


def run(stage,argv):
    started=time.monotonic()
    result=subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out=result.stdout.decode(errors='replace')
    err=result.stderr.decode(errors='replace')
    row=dict(stage=stage,argv=argv,exit_code=result.returncode,seconds=time.monotonic()-started,stdout=out,stderr=err)
    records.append(row)
    (BUILD/'build-record.json').write_text(json.dumps(records,indent=2)+'\n')
    if result.returncode:raise RuntimeError(stage+' failed: '+err)
    return out


def main():
    PACKAGE.mkdir(exist_ok=False)
    run('container-state',['docker','inspect','--format','{{.Id}} {{.State.Status}} {{.Config.Image}}',CONTAINER])
    run('compiler-version',['docker','exec',CONTAINER,'aarch64-linux-gnu-gcc','--version'])
    run('objdump-version',['docker','exec',CONTAINER,'aarch64-linux-gnu-objdump','--version'])
    run('fresh-container-directory',['docker','exec',CONTAINER,'mkdir',REMOTE])
    run('copy-c-source',['docker','cp',str(ROOT/'native/mmio32.c'),CONTAINER+':'+REMOTE+'/mmio32.c'])
    run('aarch64-shared-build',['docker','exec',CONTAINER,'aarch64-linux-gnu-gcc',
        '-std=c11','-O2','-Wall','-Wextra','-Werror','-fPIC','-fvisibility=hidden','-shared',
        '-Wl,-z,defs','-Wl,-z,relro,-z,now','-Wl,--build-id=none',
        REMOTE+'/mmio32.c','-o',REMOTE+'/libmmio32.so'])
    run('copy-aarch64-library',['docker','cp',CONTAINER+':'+REMOTE+'/libmmio32.so',str(PACKAGE/'libmmio32.so')])
    disassembly=run('aarch64-disassembly',['docker','exec',CONTAINER,'aarch64-linux-gnu-objdump','-d',REMOTE+'/libmmio32.so'])
    (BUILD/'aarch64-objdump.txt').write_text(disassembly)
    dynamic=run('aarch64-dynamic',['docker','exec',CONTAINER,'aarch64-linux-gnu-readelf','-h','-d',REMOTE+'/libmmio32.so'])
    (BUILD/'aarch64-readelf.txt').write_text(dynamic)
    run('host-compiler-version',['gcc','--version'])
    run('host-DLL-build',['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-shared',
         str(ROOT/'native/mmio32.c'),'-o',str(BUILD/'mmio32-host.dll')])
    identities={str(path.relative_to(ROOT)):dict(bytes=path.stat().st_size,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in
        (ROOT/'native/mmio32.c',PACKAGE/'libmmio32.so',BUILD/'mmio32-host.dll')}
    (BUILD/'native-identities.json').write_text(json.dumps(identities,indent=2)+'\n')
    print(json.dumps(dict(compiled=True,SDK_loaded=False,board_access=False,identities=identities)))


if __name__=='__main__':main()
