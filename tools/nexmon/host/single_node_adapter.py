"""Single-node physical-bin mapping and explicit fixed empirical gain.

This is a PC-side input adapter, not model preprocessing. A fixed shared real
gain preserves phase and relative amplitudes across time/carriers/RX chains.
It aligns numeric scale, not absolute RF power or cross-device pose accuracy.
"""
import json
from pathlib import Path

import numpy as np

from map_node_windows import HT20_NG2
from native_carriers import select_packed, decode_selected


def packet_rms(csi, chain_axis=-3, carrier_axis=-2):
    a=np.asarray(csi)
    if not np.iscomplexobj(a) or not np.isfinite(a).all():
        raise ValueError('Expected finite complex CSI')
    return np.sqrt(np.mean(np.abs(a)**2,axis=(chain_axis,carrier_axis)))


class SingleNodeAdapter:
    def __init__(self,profile):
        if isinstance(profile,(str,Path)):
            profile=json.loads(Path(profile).read_text(encoding='utf-8'))
        self.profile=profile
        if (profile.get('schema')!=1 or profile.get('method')!='fixed_shared_empirical_gain' or
                tuple(profile.get('signed_carriers',()))!=HT20_NG2 or
                profile.get('receiver_nodes')!=1 or profile.get('physical_power_calibrated') is not False):
            raise ValueError('Unsupported or mislabelled single-node calibration profile')
        self.gain=float(profile['gain'])
        if not np.isfinite(self.gain) or self.gain<=0:
            raise ValueError('Gain must be finite, positive and fixed')

    def apply(self,csi):
        a=np.asarray(csi)
        if a.shape[-3:]!=(3,30,20) or not np.iscomplexobj(a) or not np.isfinite(a).all():
            raise ValueError('Require finite single-node [...,3,30,20] CSI')
        if np.any(packet_rms(a)<=0):
            raise ValueError('Zero-power reception cannot be calibrated')
        result=a*self.gain
        if not np.isfinite(result).all():
            raise ValueError('Calibration produced non-finite CSI')
        return result

    def map_window(self,window,source_mac,channel):
        if (source_mac.lower()!=self.profile['transmitter_mac'] or
                int(channel)!=self.profile['chanspec']):
            raise ValueError('Calibration source/channel identity mismatch')
        if not window.valid or len(window.observations)!=20:
            raise ValueError('Incomplete/rejected time window')
        packed=[]
        for o in window.observations:
            if o is None:
                raise ValueError('Missing observation; no padding permitted')
            packed.append(select_packed(o.payload,HT20_NG2,o.original_words))
        native=decode_selected(np.asarray(packed,dtype='u4')).transpose(1,2,0)
        return self.apply(native)
