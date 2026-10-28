"""One exclusive GPU per finite comparison arm; complete evaluations then exit."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('--name',required=True)
    p.add_argument('--initialization',required=True,choices=['finetune','scratch']);p.add_argument('--gpu',required=True);p.add_argument('--detach',action='store_true');a=p.parse_args()
    root=a.root.resolve();run=root/a.name;tools=root/'tools';algo=Path('/public/cyd/Person-in-WiFi-3D-repo')
    if not a.gpu.isdigit():raise ValueError('Exactly one physical GPU required')
    launch=root/(a.name+'-launch.json');status_path=root/(a.name+'-status.json')
    if a.detach:
        if launch.exists():raise ValueError('Arm already launched')
        with (root/(a.name+'-console.log')).open('x') as log:
            command=[sys.executable,str(Path(__file__).resolve()),'--root',str(root),'--name',a.name,'--initialization',a.initialization,'--gpu',a.gpu]
            child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,cwd=algo)
        with launch.open('x') as out:json.dump(dict(pid=child.pid,command=command,started=time.time(),max_gpus=1,max_epochs=30,training_budget_seconds=4800),out,indent=2)
        print('Launched',a.name,'PID',child.pid,'GPU',a.gpu,flush=True);sys.exit(0)
    stage='preparing';started=time.time()
    env=os.environ.copy();env.update(CUDA_VISIBLE_DEVICES=a.gpu,OMP_NUM_THREADS='2',MKL_NUM_THREADS='2')
    def save(**kw):
        tmp=status_path.with_suffix('.tmp');tmp.write_text(json.dumps(dict(stage=stage,pid=os.getpid(),gpu=a.gpu,initialization=a.initialization,
            time=time.time(),elapsed_seconds=time.time()-started,training_started=(run/'initialization.json').exists(),**kw),indent=2)+'\n');tmp.replace(status_path)
    def execute(command,filename):
        log=root/(a.name+'-'+filename+'.log')
        with log.open('x') as stream:
            child=subprocess.Popen(command,cwd=algo,env=env,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT)
            save(child_pid=child.pid,command=command,log=str(log));rc=child.wait()
        if rc:raise RuntimeError('Native exit '+str(rc)+'; '+str(log))
    def distributed(script,*args):return [sys.executable,'-m','torch.distributed.run','--standalone','--nproc_per_node=1',str(tools/script),*map(str,args)]
    try:
        save()
        inventory=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid','--format=csv,noheader,nounits'],text=True)
        mapping={line.split(',')[0].strip():line.split(',')[1].strip() for line in inventory.splitlines()}
        active=subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid,pid','--format=csv,noheader,nounits'],text=True)
        if a.gpu not in mapping or any(line.split(',')[0].strip()==mapping[a.gpu] for line in active.splitlines()):raise ValueError('Selected GPU is absent or occupied')
        if not (root/'transfer-verified.json').exists():raise ValueError('Dataset transfer not verified')
        execute([sys.executable,str(tools/'configure_fast_run.py'),'--root',str(root),'--algorithm',str(algo),'--run-name',a.name,'--initialization',a.initialization,'--local-only','--batch-size','32','--epochs','30'],'configuration')
        stage='baseline';execute(distributed('evaluate_fast.py','--run',run,'--output',run/'baseline.json'),'baseline')
        stage='training';execute(distributed('fast_train_entry.py',run/'config.py','--launcher','pytorch','--seed','0'),'training')
        rows=[json.loads(line) for line in (run/'validation.jsonl').read_text().splitlines()]
        epoch=min(range(len(rows)),key=lambda i:rows[i]['metrics']['top1_mpjpe'])+1
        best=run/('best_top1_mpjpe_epoch_'+str(epoch)+'.pth')
        if not best.exists():raise FileNotFoundError(best)
        stage='full_validation';execute(distributed('evaluate_fast.py','--run',run,'--checkpoint',best,'--maximum','0','--output',run/'full-validation.json'),'full-validation')
        stage='held_out_test';execute(distributed('evaluate_fast.py','--run',run,'--checkpoint',best,'--split','test','--maximum','0','--output',run/'held-out-test.json'),'test')
        stage='completed';save(best_epoch=epoch,completed_epochs=len(rows),best_checkpoint=str(best),
            validation=json.loads((run/'full-validation.json').read_text())['metrics'],test=json.loads((run/'held-out-test.json').read_text())['metrics'],
            site_calibration_verified=False,official_layout_adaptation=False,board_deployment=False)
    except Exception as error:
        save(failed=True,error=type(error).__name__+': '+str(error));raise
