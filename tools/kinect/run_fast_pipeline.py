"""Managed finite pipeline: verify transfer, baseline, train, held-out evaluation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import zipfile


def save(path,value):
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(value,indent=2)+'\n');temporary.replace(path)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('--gpus',required=True);p.add_argument('--detach',action='store_true');a=p.parse_args()
    root=a.root.resolve();algo=Path('/public/cyd/Person-in-WiFi-3D-repo');tools=root/'tools';run=root/'run'
    if a.detach:
        if (root/'pipeline-launch.json').exists():raise ValueError('Pipeline already launched; inspect it instead of duplicating')
        with (root/'pipeline-console.log').open('x') as log:
            command=[sys.executable,str(Path(__file__).resolve()),'--root',str(root),'--gpus',a.gpus]
            child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,cwd=algo)
        launch=dict(pid=child.pid,command=command,started=time.time(),bounded_epochs=8)
        with (root/'pipeline-launch.json').open('x') as out:json.dump(launch,out,indent=2)
        print(json.dumps(launch),flush=True);sys.exit(0)
    stage='verification';started=time.time();child=None
    env=os.environ.copy();env.update(CUDA_VISIBLE_DEVICES=a.gpus,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
    ids=a.gpus.split(',');world=len(ids)
    def status(**kw):save(root/'pipeline-status.json',dict(stage=stage,pid=os.getpid(),time=time.time(),elapsed_seconds=time.time()-started,**kw))
    def execute(command,log):
        global child
        status(command=command,log=str(log),training_started=(root/'run/initialization.json').exists())
        with log.open('x') as stream:
            child=subprocess.Popen(command,cwd=algo,env=env,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT)
            status(child_pid=child.pid,command=command,log=str(log),training_started=(root/'run/initialization.json').exists())
            rc=child.wait();child=None
        if rc:raise RuntimeError('Native exit '+str(rc)+'; see '+str(log))
    def distributed(script,*args):return [sys.executable,'-m','torch.distributed.run','--standalone','--nproc_per_node='+str(world),str(tools/script),*map(str,args)]
    try:
        status()
        inventory=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid','--format=csv,noheader,nounits'],text=True)
        byindex={line.split(',')[0].strip():line.split(',')[1].strip() for line in inventory.splitlines()}
        if len(set(ids))!=world or not set(ids)<=set(byindex):raise ValueError('GPU selection invalid')
        active=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True)
        if any(line.split(',')[0].strip() in {byindex[i] for i in ids} for line in active.splitlines()):raise ValueError('Selected GPU occupied; no existing job is interrupted')
        manifest=json.loads((root/'archive.json').read_text());archive=root/'dataset.zip';digest=hashlib.sha256()
        with archive.open('rb') as source:
            for block in iter(lambda:source.read(8*1024**2),b''):digest.update(block)
        if archive.stat().st_size!=manifest['bytes'] or digest.hexdigest()!=manifest['sha256']:raise ValueError('Transferred archive identity mismatch')
        with zipfile.ZipFile(archive) as data:
            for item in data.infolist():
                target=(root/item.filename).resolve()
                if root not in target.parents or target.exists():raise ValueError('Unsafe/duplicate extraction target '+str(target))
            data.extractall(root)
        save(root/'transfer-verified.json',dict(bytes=manifest['bytes'],sha256=manifest['sha256'],extracted=True))
        if not (root/'dataset/official_train_data/cache.json').exists():raise ValueError('Official cache unfinished')
        execute([sys.executable,str(tools/'configure_fast_run.py'),'--root',str(root),'--algorithm',str(algo),'--epochs','8'],root/'configuration.log')
        stage='baseline';execute(distributed('evaluate_fast.py','--run',run,'--maximum','1200','--output',run/'baseline.json'),root/'baseline-console.log')
        stage='training';execute(distributed('fast_train_entry.py',run/'config.py','--launcher','pytorch','--seed','0'),root/'training-console.log')
        records=[json.loads(line) for line in (run/'validation.jsonl').read_text().splitlines()]
        best_epoch=min(range(len(records)),key=lambda i:records[i]['metrics']['top1_mpjpe'])+1
        best=run/('best_top1_mpjpe_epoch_'+str(best_epoch)+'.pth')
        if not best.is_file():raise FileNotFoundError(best)
        stage='full_validation';execute(distributed('evaluate_fast.py','--run',run,'--checkpoint',best,'--maximum','0','--output',run/'full-validation.json'),root/'full-validation-console.log')
        stage='original_test';execute(distributed('evaluate_fast.py','--run',run,'--split','test','--maximum','0','--output',run/'original-test.json'),root/'original-test-console.log')
        stage='finetuned_test';execute(distributed('evaluate_fast.py','--run',run,'--checkpoint',best,'--split','test','--maximum','0','--output',run/'finetuned-test.json'),root/'finetuned-test-console.log')
        stage='completed';status(training_started=True,best_checkpoint=str(best),best_epoch=best_epoch,
            original_test=json.loads((run/'original-test.json').read_text())['metrics'],
            finetuned_test=json.loads((run/'finetuned-test.json').read_text())['metrics'],
            site_calibration_verified=False,official_coordinate_equivalence_verified=False,board_deployment=False)
    except Exception as error:
        status(failed=True,error=type(error).__name__+': '+str(error),training_started=(run/'initialization.json').exists())
        raise
