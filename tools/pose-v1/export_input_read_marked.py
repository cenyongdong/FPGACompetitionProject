"""Bind each sampled source to Native marked bytes, using existing diagnostics."""
import subprocess,json
from pathlib import Path
root=Path(__file__).resolve().parents[2];docker='C:/Program Files/Docker/Docker/resources/bin/docker.exe';remote='/tmp/pose-v1-mixed-20261010-input-read-r1';e=root/'tools/pose-v1/evidence/input-read-20261010-r1'
out=e/'native-marked';assert not out.exists();out.mkdir();samples=[json.loads(x) for x in (e/'picture-return/run-picture/results/vpu/samples.jsonl').read_text().splitlines()]
manifest=out/'sample-manifest.tsv';manifest.write_text(''.join(str(x['encoded_id'])+' '+(f"result{x['invocation']}.nv12" if x['inference_result'] else 'warmup.nv12')+'\n' for x in samples),newline='\n')
commands=[['cp',str(root/'tools/pose-v1/picture_marked_reference.cpp'),'FPAI:'+remote+'/picture_marked_reference.cpp'],['cp',str(manifest),'FPAI:'+remote+'/sample-manifest.tsv'],['exec','FPAI','g++','-std=c++17','-O2','-Wall','-Wextra','-Wpedantic','-Werror','-I'+remote+'/source',remote+'/picture_marked_reference.cpp',remote+'/source/picture_marker.cpp','-o',remote+'/build/picture-marked.native'],['exec','FPAI',remote+'/build/picture-marked.native',remote+'/reference-output',remote+'/sample-manifest.tsv'],['cp','FPAI:'+remote+'/build/picture-marked.native',str(out/'picture-marked.native')]]
for i,c in enumerate(commands):
    p=subprocess.run([docker,*c],capture_output=True);(out/f'step{i}.stdout.log').write_bytes(p.stdout);(out/f'step{i}.stderr.log').write_bytes(p.stderr);assert p.returncode==0,p.stderr.decode(errors='replace')
rows=[line.split() for line in (out/'step3.stdout.log').read_text().splitlines()];assert len(rows)==len(samples)
for (id,digest),s in zip(rows,samples):assert int(id)==s['encoded_id'] and digest==s['marked_NV12_fnv1a64']
report=dict(status='all_sampled_marked_NV12_diagnostic_hashes_match_Native',samples=len(rows),FNV_is_not_cryptographic_proof=True,scope='Unmarked NV12 separately compared byte-for-byte; this binds exact frozen marker function and source association.')
(out/'review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print(report['status'],len(rows))
