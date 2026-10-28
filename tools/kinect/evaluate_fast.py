"""Finite distributed actual-input evaluation; no optimizer or model changes."""
import argparse,json,os,sys,time
from pathlib import Path
import numpy as np
import torch
import torch.distributed as dist

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',required=True,type=Path);p.add_argument('--checkpoint',type=Path)
    p.add_argument('--split',default='val',choices=['val','test']);p.add_argument('--maximum',type=int,default=1200);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();run=a.run.resolve();plan=json.loads((run/'preparation.json').read_text());sys.path.insert(0,plan['algorithm_root'])
    torch.set_num_threads(2);rank=int(os.environ.get('LOCAL_RANK','0'));torch.cuda.set_device(rank);torch.cuda.set_per_process_memory_fraction(.85,rank)
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    dist.init_process_group('nccl');rank=dist.get_rank();world=dist.get_world_size()
    from mmcv import Config
    from opera.models import build_model
    from opera.datasets import build_dataset
    cfg=Config.fromfile(str(run/'config.py'))
    from opera.apis import set_random_seed
    set_random_seed(0,deterministic=False)
    model=build_model(cfg.model);model.init_weights()
    checkpoint=a.checkpoint or (Path(plan['starting_checkpoint']) if plan['starting_checkpoint'] else None)
    if a.checkpoint:
        state=torch.load(checkpoint,map_location='cpu');state=state.get('state_dict',state)
        state={k[7:] if k.startswith('module.') else k:v for k,v in state.items()};model.load_state_dict(state,strict=True)
    model.cuda().eval();data_root=Path(plan['dataset'])/(a.split+'_data')
    from fast_training import KinectWifiMemmapDataset
    ds=KinectWifiMemmapDataset(str(data_root),[],mode='test',maximum_samples=a.maximum or None)
    # Check the real configured training and validation formatting once.
    if rank==0 and not (run/'actual-data-readiness.json').exists():
        train=build_dataset(cfg.data.train);parts=getattr(train,'datasets',[train])
        for part in parts:_=part[0]
        validation=build_dataset(cfg.data.val);_=validation[0]
        with torch.no_grad():
            x=torch.from_numpy(np.array(ds._tokens[ds.row_indices[:8]],copy=True)).cuda()
            score,pose=model.predict_tokens(x)
            one=[model.predict_tokens(v[None]) for v in x]
            batch_delta=float((pose-torch.cat([v[1] for v in one])).abs().max())
            native=model.simple_test(x.reshape(-1,3,3,20,60),[{} for _ in x])
            native_pose=np.array([v[1][0] for v in native])
            native_delta=float(np.max(np.abs(native_pose-pose.cpu().numpy())))
            if not np.isfinite(batch_delta) or batch_delta>.01 or native_delta>.001:
                (run/'batch-check-failure.json').write_text(json.dumps(dict(batch_delta=batch_delta,native_delta=native_delta)))
                raise ValueError('Batch inference numerical check failed')
        (run/'actual-data-readiness.json').write_text(json.dumps(dict(local=len(parts[0]),official=sum(len(x) for x in parts[1:]),validation=len(validation),
            batch1_batch8_max_coordinate_difference_m=batch_delta,native_predict_tokens_max_difference_m=native_delta,
            strict_loaded_tensors=model.migration_report['loaded'],actual_pipelines_passed=True),indent=2)+'\n')
    dist.barrier();start=time.time();rows=list(range(rank,len(ds),world));sums=torch.zeros(8,device='cuda',dtype=torch.float64)
    record_totals={}
    with torch.no_grad():
        for start_index in range(0,len(rows),8):
            batch=rows[start_index:start_index+8];source_rows=ds.row_indices[batch]
            x=torch.from_numpy(np.array(ds._tokens[source_rows],copy=True)).cuda();gt=torch.from_numpy(np.array(ds._poses[source_rows,0],copy=True)).cuda()
            scores,poses=model.predict_tokens(x)
            if not torch.isfinite(poses).all() or not torch.isfinite(scores).all():raise ValueError('Nonfinite inference')
            dif=poses-gt[:,None];distances=torch.linalg.vector_norm(dif,dim=-1).mean(-1);ids=scores.argmax(-1);best=distances.argmin(-1);b=torch.arange(len(batch),device='cuda')
            top=distances[b,ids]*1000;minimum=distances[b,best]*1000
            dims=dif[b,best].abs().mean(1)*1000
            selected=poses[b,ids];pred_root=selected[:,[5,7]].mean(1);gt_root=gt[:,[5,7]].mean(1)
            root_error=torch.linalg.vector_norm(pred_root-gt_root,dim=-1)*1000
            relative_error=torch.linalg.vector_norm((selected-pred_root[:,None])-(gt-gt_root[:,None]),dim=-1).mean(-1)*1000
            sums+=torch.cat([minimum.sum()[None],top.sum()[None],dims.sum(0),root_error.sum()[None],relative_error.sum()[None],torch.tensor([len(batch)],device='cuda')]).double()
            for j,k in enumerate(batch):
                name=ds.filename_list[k].rsplit('_',1)[0];v=record_totals.setdefault(name,[0.,0.,0]);v[0]+=float(top[j]);v[1]+=float(minimum[j]);v[2]+=1
    dist.all_reduce(sums);per_rank=[None]*world;dist.all_gather_object(per_rank,record_totals)
    if rank==0:
        total=sums.cpu().numpy();n=int(total[-1]);assert n==len(ds)
        metrics=dict(mpjpe=float(total[0]/n),top1_mpjpe=float(total[1]/n),mpjpeh=float(total[2]/n),mpjpev=float(total[3]/n),mpjped=float(total[4]/n),
            top1_hip_center_error_mm=float(total[5]/n),top1_root_relative_mpjpe_mm=float(total[6]/n))
        merged={}
        for part in per_rank:
            for key,v in part.items():merged[key]=np.array(merged.get(key,[0.,0.,0]))+v
        result=dict(checkpoint=str(checkpoint),split=a.split,frames=n,full_split_frames=ds.full_count,fixed_subset=n!=ds.full_count,metrics=metrics,
            per_recording={k:dict(top1_mpjpe=float(v[0]/v[2]),mpjpe=float(v[1]/v[2]),frames=int(v[2])) for k,v in merged.items()},
            elapsed_seconds=time.time()-start,TF32=False,training_steps=0,site_calibration_verified=False)
        if not a.checkpoint:result['initialization']=model.migration_report
        with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
        print(json.dumps(result),flush=True)
    dist.barrier();dist.destroy_process_group()
