"""Fresh FPAI build with verified source aliases; no board/model execution."""
from pathlib import Path
import argparse, hashlib, json, re, shutil, subprocess

ROOT = Path(__file__).resolve().parents[2]
DEMO = Path(__file__).resolve().parent
VENDOR = Path(r'D:\Dowload from Chrome\嵌赛资料\Icraft\参考实现\单路PLIM+VPU\fpai_demo_package_26040702\fpai_demo_package_26040702\deps\thirdparty')
DOCKER = r'C:\Program Files\Docker\Docker\resources\bin\docker.exe'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--tag',default='demo-20261011-r1');a=parser.parse_args()
    assert re.fullmatch(r'demo-[a-zA-Z0-9_-]+',a.tag)
    out=ROOT/'.local/pose-v1-build'/a.tag;assert not out.exists();out.mkdir()
    lock=json.loads((DEMO/'baseline-lock.json').read_text(encoding='utf-8'))
    baseline=out/'baseline';baseline.mkdir()
    for rel,item in lock['build_files'].items():
        assert sha(ROOT/rel)==item['sha256'],rel
        assert Path(item['destination']).name==item['destination']
        shutil.copyfile(ROOT/rel,baseline/item['destination'])
    for rel,digest in lock['vendor_files'].items():assert sha(VENDOR/rel)==digest,rel
    source=out/'demo';shutil.copytree(DEMO,source)
    remote='/tmp/pose-'+a.tag+'-build'
    def run(*args):
        p=subprocess.run([DOCKER,*args],capture_output=True)
        with (out/'build.log').open('ab') as f:f.write((repr(args)+'\n').encode()+p.stdout+p.stderr)
        if p.returncode:raise RuntimeError(p.stderr[-4000:].decode(errors='replace'))
        return p.stdout
    run('exec','FPAI','test','!','-e',remote);run('exec','FPAI','mkdir',remote)
    run('cp',str(baseline),'FPAI:'+remote+'/baseline');run('cp',str(source),'FPAI:'+remote+'/demo')
    snapshot=out/'sdk';snapshot.mkdir()
    for rel,digest in lock['sdk_headers_normalized_sha256'].items():
        dest=snapshot/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        run('cp','-L','FPAI:/usr/include/'+rel,str(dest))
        assert hashlib.sha256(dest.read_bytes().replace(b'\r\n',b'\n')).hexdigest()==digest
    for package in ('icraft:arm64','customop:arm64'):
        assert run('exec','FPAI','dpkg-query','-W','-f=${Version}',package).strip()==b'3.39.0'
    libraries={}
    for name in ('libicraft_hostbackend.so','libicraft_zg330backend.so','libicraft_xrt.so','libicraft_xir.so','libicraft_utils.so','libaxizg330aiu.so'):
        run('cp','-L','FPAI:/usr/lib/aarch64-linux-gnu/'+name,str(snapshot/name));libraries[name]=sha(snapshot/name)
    assert libraries['libicraft_hostbackend.so']==lock['host_library_sha256']
    assert libraries['libicraft_zg330backend.so']==lock['zg_library_sha256']
    run('exec','FPAI','mkdir','-p',remote+'/vendor/libs')
    for rel in ('include/live','include/openssl'):run('cp',str(VENDOR/rel),'FPAI:'+remote+'/vendor/'+Path(rel).name)
    for rel in lock['vendor_files']:
        if rel.startswith('a/'):run('cp',str(VENDOR/rel),'FPAI:'+remote+'/vendor/libs/'+Path(rel).name)
    flags=['-std=gnu++17','-O2','-DNDEBUG','-pthread','-I'+remote+'/baseline']
    run('exec','FPAI','g++',*flags,remote+'/baseline/tcp_receiver.cpp',remote+'/baseline/tcp_transport_check.cpp','-o',remote+'/transport-native')
    (out/'transport-native.txt').write_bytes(run('exec','FPAI',remote+'/transport-native','--self-test'))
    run('exec','FPAI','cmake','-S',remote+'/demo','-B',remote+'/build',
        '-DCMAKE_SYSTEM_NAME=Linux','-DCMAKE_SYSTEM_PROCESSOR=aarch64',
        '-DCMAKE_CXX_COMPILER=aarch64-linux-gnu-g++','-DCMAKE_BUILD_TYPE=Release',
        '-DCMAKE_CXX_FLAGS_RELEASE=-O2 -DNDEBUG','-DCMAKE_PREFIX_PATH=/usr/cmake',
        '-DBASELINE_DIR='+remote+'/baseline','-DVENDOR_DIR='+remote+'/vendor')
    run('exec','FPAI','cmake','--build',remote+'/build','--parallel','2')
    programs={}
    for name in ('pose_demo','pose_display_worker','pose_demo_transport_test'):
        run('cp','FPAI:'+remote+'/build/'+name,str(out/name));programs[name]=sha(out/name)
    (out/'needed.txt').write_bytes(run('exec','FPAI','aarch64-linux-gnu-readelf','-d',remote+'/build/pose_demo'))
    report={'status':'compiled_not_board_executed','programs':programs,'libraries':libraries,
            'baseline_manifest_sha256':sha(DEMO/'baseline-lock.json'),
            'baseline_sources':{p:v['sha256'] for p,v in lock['build_files'].items()},
            'demo_sources':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(DEMO.rglob('*')) if p.is_file() and '__pycache__' not in p.parts},
            'vendor_files':lock['vendor_files'],'sdk_headers_normalized_sha256':lock['sdk_headers_normalized_sha256'],
            'graph_sha256':lock['graph_sha256'],'raw_sha256':lock['raw_sha256'],
            'HDMI':False,'prior_Host107_reused':True,'new_Host107_executed':False}
    (out/'build-result.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Demo built',out,programs['pose_demo'])
if __name__=='__main__':main()
