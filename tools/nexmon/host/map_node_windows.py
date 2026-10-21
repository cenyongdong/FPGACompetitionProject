"""Uncalibrated single-node HT20/Ng2 candidates, never a full model packet."""
import argparse
import json
from pathlib import Path

import numpy as np

from native_carriers import select_packed, decode_selected
from validate_dedup import read_events, select_first_valid

# IEEE n grouping, not the different compressed-feedback 'ac' grouping.
# Intel tool FAQ identifies HT20/Ng2; csiread's scidx implements this table.
HT20_NG2 = tuple(range(-28,-1,2)) + (-1,) + tuple(range(1,28,2)) + (28,)


def convert(pcap,accepted,output,profile):
    if profile!='intel-ht20-ng2':
        raise ValueError('An explicit physical carrier profile is required')
    output.mkdir(parents=True,exist_ok=False)
    events,_=read_events(pcap)
    kept=select_first_valid(events)
    by_index={e.index:e for e in kept}
    with np.load(accepted) as z:
        ids=z['original_event_indices'].astype('i8')
    if ids.ndim!=2 or ids.shape[1]!=20 or len(np.unique(ids))!=ids.size:
        raise ValueError('Require nonoverlapping complete 20-frame index windows')
    selected=[]
    for index in ids.reshape(-1):
        e=by_index.get(int(index))
        if e is None or e.meta['channel'] & 0x3800 != 0x1000:
            raise ValueError('Invalid first-valid source or bandwidth')
        selected.append(select_packed(e.words,HT20_NG2,e.original_words))
    packed=np.asarray(selected,dtype='u4').reshape(len(ids),20,3,30)
    candidate=decode_selected(packed).transpose(0,2,3,1)
    if not np.isfinite(candidate).all():
        raise ValueError('Non-finite mapped CSI')
    np.savez_compressed(output/'single-node-windows.npz',csi_uncalibrated=candidate,
        original_event_indices=ids,signed_subcarriers=np.asarray(HT20_NG2,dtype='i4'))
    result=dict(model_ready=False,receiver_nodes=1,shape=list(candidate.shape),
        axes=['window','rx_chain','physical_subcarrier','time'],dtype=str(candidate.dtype),
        profile=profile,signed_carriers=HT20_NG2,raw_indices=[k%64 for k in HT20_NG2],
        positive28_source='Paired NMD2 pre-PHY-overwrite word, per core; no neighbor substitution',
        all_selected_frames_first_valid=True,all_values_finite=True,
        temporal_interpolation=False,frequency_interpolation=False,node_replication=False,
        calibrated=False,training_dataset_binding_verified=False,
        sources=['https://dhalperi.github.io/linux-80211n-csitool/faq.html',
            'https://github.com/citysu/csiread/blob/master/csiread/utils.py'],
        limitations=['Explicit standard Intel HT20/Ng2 candidate profile, not proof the released training MAT files have no extra reordering.',
            'No receiver gain/noise/reference amplitude alignment, no pose inference or accuracy assessment.',
            'One node only; never fill the required three-node axis with copies.'])
    (output/'summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('pcap',type=Path);p.add_argument('--accepted',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--profile',required=True,choices=['intel-ht20-ng2'])
    a=p.parse_args();r=convert(a.pcap,a.accepted,a.output,a.profile)
    print(json.dumps(r,indent=2))
