"""Fresh F0 finite integration package; validated model/fixtures/core preserved."""
import argparse,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    base=ROOT/'.local/pose-v1-render/package-20261007-r1';old=json.loads((base/'manifest.json').read_text())
    for line in (base/'files.sha256').read_text().splitlines():
        digest,name=line.split('  ',1);assert sha(base/name)==digest,name
    keep={'mixed_bridge.hpp','mixed_fusion_baseline.hpp','content_diagnostic.hpp','mixed_host_check.cpp','host_cpu_adapter.hpp','preprocess.hpp','preprocess.cpp','toolchain.cmake','host_cpu_adapter.cpp','lazy_runtime_validation.hpp','application_core.hpp','application_core.cpp','application_bridge.cpp','application_clock.hpp','skeleton_render.hpp','skeleton_render.cpp'}
    build={}
    for name,value in old['build_files'].items():
        if value['destination'] in keep:
            assert sha(ROOT/name)==value['sha256'],'Frozen core source changed: '+name
            build[name]=value
    for name,dest in [('software/pose_v1/include/vpu_encoder.hpp','vpu_encoder.hpp'),
                      ('software/pose_v1/include/vpu_pipeline_encoder.hpp','vpu_pipeline_encoder.hpp'),
                      ('software/pose_v1/src/vpu_pipeline_encoder.cpp','vpu_pipeline_encoder.cpp'),
                      ('software/pose_v1/src/pipeline_encode_check.cpp','pipeline_encode_check.cpp'),
                      ('tools/pose-v1/pipeline-CMakeLists.txt','CMakeLists.txt')]:
        build[name]={'destination':dest,'sha256':sha(ROOT/name)}
    a.output.mkdir(parents=True)
    for name in ('graph','fixtures','inputs','reference','r6-reference'):shutil.copytree(base/name,a.output/name)
    for name in ('cases.tsv','cpu-fixture-manifest.json'):shutil.copyfile(base/name,a.output/name)
    for name in ('board_application_preflight.py','run-pipeline-stage.sh'):shutil.copyfile(ROOT/'tools/pose-v1'/name,a.output/name)
    keys=('sdk_headers_normalized_sha256','host_library_sha256','zg_library_sha256')
    m={key:old[key] for key in keys}
    m.update(scope='F0-A1 finite serial Engine -> renderer -> VPU; not realtime/RTSP',build_files=build,
             model_payload_source_manifest_sha256=sha(base/'manifest.json'),frames=10,warmup_frames=2,regression_calls=4,production_calls=4,
             fixed_cases=['S11_01_308','S11_01_309','S11_01_310','S11_01_308'],
             frozen_vpu_r5_sha256=sha(ROOT/'software/pose_v1/src/vpu_encoder.cpp'),
             sources={name:sha(ROOT/name) for name in ('tools/pose-v1/prepare_pipeline_package.py','tools/pose-v1/Build-Pipeline.ps1','tools/pose-v1/run-pipeline-stage.sh','tools/pose-v1/pipeline-CMakeLists.txt')})
    (a.output/'manifest.json').write_bytes((json.dumps(m,indent=2)+'\n').encode())
    files=sorted(p for p in a.output.rglob('*') if p.is_file())
    (a.output/'files.sha256').write_bytes(''.join(f'{sha(p)}  {p.relative_to(a.output).as_posix()}\n' for p in files).encode())
    print('F0 package prepared',len(files),'payloads;',len(build),'build sources',a.output)

if __name__=='__main__':main()
