import argparse,json,sys
from pathlib import Path
import numpy as np
import torch

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',required=True,type=Path);a=p.parse_args();plan=json.loads((a.run/'preparation.json').read_text());sys.path.insert(0,plan['algorithm_root'])
    torch.set_num_threads(2);torch.cuda.set_device(0);torch.cuda.set_per_process_memory_fraction(.75)
    from mmcv import Config
    from opera.models import build_model
    cfg=Config.fromfile(str(a.run/'config.py'));m=build_model(cfg.model);m.init_weights();m.cuda().eval()
    data=np.load(Path(plan['dataset'])/'val_data/tokens.npy',mmap_mode='r');x=torch.from_numpy(np.array(data[:8],copy=True)).cuda()
    records=[]
    with torch.no_grad():
        for tf32 in [True,False]:
            torch.backends.cuda.matmul.allow_tf32=tf32;torch.backends.cudnn.allow_tf32=tf32
            s,p=m.predict_tokens(x);one=[m.predict_tokens(v[None]) for v in x]
            n=m.simple_test(x.reshape(-1,3,3,20,60),[{} for _ in x]);np_=np.asarray([z[1][0] for z in n]);ns=np.asarray([z[0][0][:,-1] for z in n])
            r=dict(tf32=tf32,pose_max_difference=float((p-torch.cat([z[1] for z in one])).abs().max()),
                scores_max_difference=float((s-torch.cat([z[0] for z in one])).abs().max()),native_pose_max_difference=float(np.max(np.abs(np_-p.cpu().numpy()))),
                native_score_max_difference=float(np.max(np.abs(ns-s.cpu().numpy()))),native_shape=list(np_.shape))
            records.append(r);print(json.dumps(r),flush=True)
    (a.run/'batch-diagnostic.json').write_text(json.dumps(records,indent=2)+'\n')
