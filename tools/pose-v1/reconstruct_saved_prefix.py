"""Native references for a proven-correct prefix; missing ARM evidence stays missing."""
import argparse,json,subprocess,shutil,re,hashlib
from pathlib import Path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--results',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--failure-review',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--tag',required=True);a=p.parse_args();assert not a.output.exists() and re.fullmatch('[a-z0-9-]+',a.tag)
    f=json.loads(a.failure_review.read_text());assert f['status']=='finite_pose_failure_complete_values_verified_not_acceptance' and f['correct_prefix_calls']==37
    b=json.loads((a.build/'build-result.json').read_text(encoding='utf-8-sig'));assert sha(a.build/'pose_bounded_reference_export.native')==b['native_reference_sha256']
    calls=[json.loads(x) for x in (a.results/'inference.jsonl').read_text().splitlines()];assert len(calls)==37
    a.output.mkdir();inputs=a.output/'inputs';inputs.mkdir();(inputs/'plan.tsv').write_text(''.join(f"{i}\t{x['frame_id']}\n" for i,x in enumerate(calls)))
    for i in range(37):
        for suffix in ('scores','poses'):shutil.copyfile(a.results/f'result{i}.{suffix}.f32',inputs/f'result{i}.{suffix}.f32')
    docker='C:/Program Files/Docker/Docker/resources/bin/docker.exe';remote='/tmp/pose-reference-'+a.tag
    def run(*args):
        r=subprocess.run([docker,*args],stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(a.output/'native.log').open('ab').write(r.stdout);assert r.returncode==0,r.stdout.decode(errors='replace')
    run('exec','FPAI','test','!','-e',remote);run('exec','FPAI','mkdir',remote);run('cp',str(inputs),'FPAI:'+remote+'/inputs');run('cp',str(a.build/'pose_bounded_reference_export.native'),'FPAI:'+remote+'/export');run('exec','FPAI','chmod','u+x',remote+'/export');run('exec','FPAI','timeout','30s',remote+'/export',remote+'/inputs/plan.tsv',remote+'/inputs',remote+'/frames');run('cp','FPAI:'+remote+'/frames',str(a.output/'frames'))
    report=dict(status='correct_prefix_Native_reconstructed_ARM_evidence_missing_not_acceptance',frames=37,ARM_sparse_reference_verified=False,ARM_references_missing=True,failure_review_sha256=sha(a.failure_review),native_program_sha256=sha(a.build/'pose_bounded_reference_export.native'),references_sha256={p.name:sha(p) for p in (a.output/'frames').iterdir()})
    (a.output/'review.json').write_text(json.dumps(report,indent=2)+'\n');print(report['status'])
if __name__=='__main__':main()
