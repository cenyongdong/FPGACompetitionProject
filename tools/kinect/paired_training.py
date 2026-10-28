"""Optional training-only adapters; never imported by the deployed service."""
import hashlib
from pathlib import Path
import numpy as np
import torch
from opera.datasets.builder import DATASETS
from opera.models.builder import DETECTORS
from opera.models.pose180.detector import PETR180
from opera.models.pose180.evaluation import WifiPose180Dataset


@DATASETS.register_module()
class KinectWifiTokenDataset(WifiPose180Dataset):
    def get_item_single_frame(self, index):
        name=self.filename_list[index]
        tokens=np.load(Path(self.data_root)/'tokens'/(name+'.npy'),allow_pickle=False)
        gt=np.load(Path(self.data_root)/'keypoint'/(name+'.npy'),allow_pickle=False)
        if tokens.shape!=(180,60) or gt.ndim!=3 or gt.shape[1:]!=(14,3) or not 1<=len(gt)<=3:
            raise ValueError('Paired input/label shape differs: '+name)
        if not np.isfinite(tokens).all() or not np.isfinite(gt).all():raise ValueError('Non-finite paired data')
        return dict(img=torch.from_numpy(tokens.astype(np.float32).reshape(3,3,20,60)),
            gt_keypoints=torch.from_numpy(gt.astype(np.float32)),gt_labels=np.zeros(len(gt),dtype=np.int64),
            gt_bboxes=torch.tensor([]),gt_areas=torch.tensor([]),img_name=name)


@DATASETS.register_module()
class KinectOfficialSubset(WifiPose180Dataset):
    def __init__(self,*args,maximum_samples=2000,**kwargs):
        super().__init__(*args,**kwargs)
        # Stable subset of official TRAIN only; no official test labels enter training.
        self.filename_list=sorted(self.filename_list,key=lambda n:hashlib.sha256(n.encode()).digest())[:maximum_samples]
        self._set_group_flag()


@DETECTORS.register_module()
class PETR180Finetune(PETR180):
    def init_weights(self):
        if self.migration_report is not None:return
        if not self.source_checkpoint:raise ValueError('Explicit original 180-query checkpoint required')
        checkpoint=torch.load(self.source_checkpoint,map_location='cpu')
        state=checkpoint.get('state_dict',checkpoint)
        state={k[7:] if k.startswith('module.') else k:v for k,v in state.items()}
        if tuple(state['bbox_head.query_embedding.weight'].shape)!=(180,512):
            raise ValueError('Use the original 180-query epoch99 checkpoint, not a 100-query checkpoint')
        if any(v.is_floating_point() and not bool(torch.isfinite(v).all()) for v in state.values()):
            raise ValueError('Non-finite starting checkpoint')
        self.load_state_dict(state,strict=True)
        self.migration_report=dict(source=str(self.source_checkpoint),source_epoch=checkpoint.get('meta',{}).get('epoch'),
            initialization_mode='strict_180_query_finetune',reinitialized=[],old_optimizer_loaded=False,
            loaded=len(state),query_shape=[180,512],
            query_sha256=hashlib.sha256(state['bbox_head.query_embedding.weight'].numpy().tobytes()).hexdigest())
        self._is_init=True
