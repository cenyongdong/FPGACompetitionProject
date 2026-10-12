"""Render returned real outputs with frozen SDK-free renderer, no board work."""
from pathlib import Path
import argparse,hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2];DOCKER=r'C:\Program Files\Docker\Docker\resources\bin\docker.exe'
def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['short','demo']);p.add_argument('--evidence',type=Path,required=True);a=p.parse_args()
    E=a.evidence.resolve();assert json.loads((E/(a.stage+'.review.json')).read_text())['status']=='end_to_end_demo_passed'
    remote='/tmp/wifi-demo-native-'+E.name+'-'+a.stage;out=E/(a.stage+'-native-render');assert not out.exists()
    def run(*args):
        r=subprocess.run([DOCKER,*args],capture_output=True)
        with (E/(a.stage+'-render-build.txt')).open('ab') as f:f.write((repr(args)+'\n').encode()+r.stdout+r.stderr)
        assert r.returncode==0,r.stderr[-2000:]
    run('exec','FPAI','test','!','-e',remote);run('exec','FPAI','mkdir',remote)
    source=ROOT/'.local/pose-v1-build/demo-20261011-r5/baseline'
    for name in ('skeleton_render.cpp','skeleton_render.hpp'):run('cp',str(source/name),'FPAI:'+remote+'/'+name)
    check=ROOT/'software/pose_v1/src/skeleton_render_check.cpp';run('cp',str(check),'FPAI:'+remote+'/render_check.cpp')
    run('cp',str(E/(a.stage+'-render-input')),'FPAI:'+remote+'/inputs');run('cp',str(E/(a.stage+'-render-catalog.tsv')),'FPAI:'+remote+'/catalog.tsv')
    run('exec','FPAI','g++','-std=gnu++17','-O2','-DNDEBUG','-ffp-contract=off','-I'+remote,remote+'/skeleton_render.cpp',remote+'/render_check.cpp','-o',remote+'/render')
    run('exec','FPAI',remote+'/render',remote+'/catalog.tsv',remote+'/inputs',remote+'/images')
    run('cp','FPAI:'+remote+'/images',str(out))
    files=[source/'skeleton_render.cpp',source/'skeleton_render.hpp',check]
    (E/(a.stage+'.render-source.json')).write_text(json.dumps({'status':'real_output_frozen_native_render_exported','sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'frames':json.loads((out/'summary.json').read_text())['frames'],'physical_devices':False},indent=2)+'\n',encoding='utf-8')
    print('Native renderer exported',a.stage)
if __name__=='__main__':main()
