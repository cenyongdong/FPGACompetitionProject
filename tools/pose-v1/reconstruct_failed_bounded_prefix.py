"""Run frozen renderer on FPAI x86 host after numeric review; never board/VPU calls."""
import argparse,hashlib,json,re,shutil,subprocess
from pathlib import Path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--results',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--numeric-review',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--tag',required=True);p.add_argument('--baseline-full',action='store_true');a=p.parse_args()
    assert not a.output.exists() and re.fullmatch('[a-zA-Z0-9-]+',a.tag)
    b=json.loads((a.build/'build-result.json').read_text(encoding='utf-8-sig'));review=json.loads(a.numeric_review.read_text());assert review['status']=='failed_bounded_load_partial_numeric_verified' and review['full_numeric_bitwise'] and (a.baseline_full or review['binary_sha256']==b['binary_sha256'])
    assert sha(a.build/'pose_bounded_reference_export.native')==b['native_reference_sha256']
    rows=[json.loads(x) for x in (a.results/'inference.jsonl').read_text().splitlines()];assert len(rows)==review['consumed']<=103
    a.output.mkdir(parents=True);inputs=a.output/'inputs';inputs.mkdir()
    (inputs/'plan.tsv').write_text(''.join(f"{i}\t{r['frame_id']}\n" for i,r in enumerate(rows)),encoding='utf-8',newline='\n')
    for i in range(len(rows)):
        for suffix in ['scores','poses']:shutil.copyfile(a.results/f'result{i}.{suffix}.f32',inputs/f'result{i}.{suffix}.f32')
    docker='C:/Program Files/Docker/Docker/resources/bin/docker.exe';remote='/tmp/pose-reference-'+a.tag
    def run(*args):
        result=subprocess.run([docker,*args],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        with (a.output/'native.log').open('ab') as f:f.write(result.stdout)
        assert result.returncode==0,result.stdout.decode(errors='replace')
    run('exec','FPAI','test','!','-e',remote);run('exec','FPAI','mkdir',remote)
    run('cp',str(inputs),'FPAI:'+remote+'/inputs');run('cp',str(a.build/'pose_bounded_reference_export.native'),'FPAI:'+remote+'/export')
    run('exec','FPAI','chmod','u+x',remote+'/export')
    run('exec','FPAI','timeout','30s',remote+'/export',remote+'/inputs/plan.tsv',remote+'/inputs',remote+'/frames')
    run('cp','FPAI:'+remote+'/frames',str(a.output/'frames'))
    assert (a.output/'frames/warmup.nv12').read_bytes()==(a.results/'frames/warmup.nv12').read_bytes()
    index=([dict(invocation=i,frame_id=r['frame_id'],ARM_postrun_reconstruction=True,sampled_buffer=False,saved=True) for i,r in enumerate(rows)] if a.baseline_full else [json.loads(x) for x in (a.results/'frames/reference-index.jsonl').read_text().splitlines()]);assert len(index)==len(rows)
    compared=[];seen=set()
    for i,(r,item) in enumerate(zip(rows,index)):
        first=r['case'] not in seen;seen.add(r['case']);expected=a.baseline_full or first or i==0 or i==27 or i+1==len(rows)
        assert item==dict(invocation=i,frame_id=r['frame_id'],ARM_postrun_reconstruction=True,sampled_buffer=False,saved=expected)
        if expected:
            assert (a.output/f'frames/result{i}.nv12').read_bytes()==(a.results/f'frames/result{i}.nv12').read_bytes();compared.append(i)
        else:assert not (a.results/f'frames/result{i}.nv12').exists()
    report=dict(status='native_frozen_renderer_references_and_sparse_ARM_bitwise',frames=len(rows),failure_prefix_only=True,baseline_full=a.baseline_full,source_program_sha256=review['binary_sha256'],sparse_compared=compared,sampled_buffers=False,native_binary_sha256=b['native_reference_sha256'],renderer_sha256=sha(a.build/'source/skeleton_render.cpp'),numeric_review_sha256=sha(a.numeric_review),inputs_sha256={p.name:sha(p) for p in inputs.iterdir()},references_sha256={p.name:sha(p) for p in (a.output/'frames').iterdir()})
    (a.output/'review.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'],len(rows),len(compared))
if __name__=='__main__':main()
