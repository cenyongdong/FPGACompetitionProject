"""Independent launcher: TF32 matmul and memory budget for exclusively free GPUs."""
import os,runpy,sys
from pathlib import Path
import torch

if __name__=='__main__':
    # The repository path is explicit in the saved run preparation.
    import json
    plan=json.loads((Path(sys.argv[1]).parent/'preparation.json').read_text())
    algorithm=Path(plan['algorithm_root']);sys.path.insert(0,str(algorithm))
    rank=int(os.environ.get('LOCAL_RANK','0'));torch.cuda.set_device(rank)
    torch.cuda.set_per_process_memory_fraction(.75,rank)
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    torch.set_num_threads(2)
    runpy.run_path(str(algorithm/'tools/train.py'),run_name='__main__')
