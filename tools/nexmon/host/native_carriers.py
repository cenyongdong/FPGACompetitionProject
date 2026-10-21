"""Explicit physical-bin selection for a single 20MHz native64 receiver node.

No default Intel/training profile is assumed. A caller must supply the signed
physical carrier list. Returned values have no AGC/noise/device calibration and
are not a complete model input. PHY-overwritten bins cannot be substituted.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from csi_verify import unpack_acphy

PHY_WORDS = (28,29,30)


def select_packed(words, signed_carriers, original_words=None):
    words=np.asarray(words)
    carriers=np.asarray(signed_carriers)
    if words.dtype.kind!='u' or words.dtype.itemsize!=4 or words.shape[-2:]!=(3,64):
        raise ValueError('Expected packed uint32 three-core native64 event(s)')
    if (carriers.dtype.kind not in 'iu' or carriers.shape!=(30,) or
            np.any(np.diff(carriers.astype('i8'))<=0) or np.any(carriers==0) or
            np.any(carriers < -28) or np.any(carriers > 28)):
        raise ValueError('Require explicit ordered 30 distinct signed carriers within HT/VHT20 occupied range')
    bins=carriers.astype('i8') % 64
    overlap=sorted(set(map(int,bins)) & set(PHY_WORDS))
    native=words
    if overlap:
        if original_words is None:
            raise ValueError('Requested physical carrier was overwritten by PHY status: '+str(overlap))
        original=np.asarray(original_words)
        if original.dtype!=words.dtype or original.shape!=words.shape[:-1]+(3,):
            raise ValueError('Require matching pre-overwrite words from paired NMD2 per core')
        native=words.copy()
        native[...,28:31]=original
    return native[...,bins].copy()


def decode_selected(packed):
    p=np.asarray(packed)
    return np.asarray(unpack_acphy(p.reshape(-1).tolist()),dtype='complex128').reshape(p.shape)


def audit(source,output):
    with np.load(source/'retained-node-events.npz') as z:
        words=z['packed_words']
    rows=[]
    for bin_id in range(64):
        a=decode_selected(words[:,:,bin_id])
        rows.append(dict(raw_word_index=bin_id,signed_carrier=bin_id if bin_id<32 else bin_id-64,
            offset_from_centre_khz=(bin_id if bin_id<32 else bin_id-64)*312.5,
            phy_overwritten=bin_id in PHY_WORDS,
            median_decoded_magnitude=float(np.median(np.abs(a)))))
    result=dict(model_ready=False,source=str(source),receiver_nodes=1,
        native_order='FFT order: raw0 DC, raw1..31 positive, raw32..63 negative; upstream plot uses fftshift',
        bandwidth_mhz=20,source_centre_mhz=5745,training_centre_mhz=5640,
        phy_overwritten_raw_words=list(PHY_WORDS),
        affected_occupied_ht20_carriers=[28],
        old_capture_can_restore_original_positive_28=False,
        remedy='NMD2 sidecar preserves original words28..30 BEFORE existing PHY overwrite; legacy CSI payload unchanged',
        training_profile_verified=False,
        remaining=['Verify exact Intel30 index/order profile from original acquisition/raw metadata.',
            'Verify pre-overwrite positive28 by live capture; do not replace with positive27 or interpolate.',
            'Establish amplitude/AGC/noise scaling versus training data; decoder is not calibrated.',
            'Different channel centres and devices remain a domain shift after physical-bin alignment.'],
        sources=dict(nexmon_plot='https://github.com/seemoo-lab/nexmon_csi/blob/1232edf2cf1e7ae0561676c49e4dd4eb22c8a27e/utils/matlab/plotcsi.m',
            nexmon_overwrite='https://github.com/seemoo-lab/nexmon_csi/blob/1232edf2cf1e7ae0561676c49e4dd4eb22c8a27e/src/csi_extractor.c',
            intel_sampling='https://dhalperi.github.io/linux-80211n-csitool/faq.html',
            training_acquisition='https://www.sdp8.net/Dataset?id=27258062-b431-438b-9d76-9052666f99ff',
            training_source='D:/Person-in-WIFI-3D/Person-in-WiFi-3D-repo/opera/datasets/wifi_pose.py'),
        bins=rows)
    with output.open('x',encoding='utf-8') as f:
        json.dump(result,f,indent=2)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=audit(a.source,a.output)
    print(json.dumps({k:v for k,v in r.items() if k!='bins'},indent=2))
