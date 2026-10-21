"""Read-only Intel 5300 raw-log/MAT correspondence audit.

Decoder follows the public Intel CSI Tool read_bfee.c/read_bf_file.m layout.
The original .dat logs stay in place; only a compact correspondence report
is written locally. No model preprocessing or radio/device access.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'software/core/input'))
from csi_io import load_mat


def read_intel(path):
    """Return [packet, RX-chain, carrier] raw CSI, with physical RX permutation."""
    raw = Path(path).read_bytes()
    position = 0
    values, metadata = [], []
    while position < len(raw):
        if len(raw) - position < 3:
            raise ValueError('Truncated Intel record header')
        length = int.from_bytes(raw[position:position+2], 'big')
        if length < 1 or position + 2 + length > len(raw):
            raise ValueError('Truncated/invalid Intel record')
        code = raw[position+2]
        p = raw[position+3:position+2+length]
        position += 2 + length
        if code != 187:
            continue
        if len(p) < 20:
            raise ValueError('Truncated beamforming header')
        nr, nt = p[8:10]
        size = int.from_bytes(p[16:18], 'little')
        expected = (30*(nr*nt*16+3)+7)//8
        if nr != 3 or nt != 1 or size != expected or len(p) != 20+size:
            raise ValueError('Require intact three-RX/one-TX Intel reference records')
        bits = np.unpackbits(np.frombuffer(p[20:], dtype='u1'), bitorder='little')
        bits = bits[:30*(3+16*nr*nt)].reshape(30, 3+16*nr*nt)[:, 3:]
        iq = bits.reshape(30, nr, nt, 2, 8) @ np.array([1,2,4,8,16,32,64,-128])
        c = (iq[..., 0] + 1j*iq[..., 1]).transpose(2,1,0)[0]
        perm = [(p[15] >> (2*i)) & 3 for i in range(nr)]
        if sorted(perm) != list(range(nr)):
            raise ValueError('Invalid Intel RX-chain permutation')
        corrected = c.copy()
        corrected[perm] = c
        values.append(corrected)
        metadata.append(dict(timestamp_low=int.from_bytes(p[:4], 'little'),
            bfee_count=int.from_bytes(p[4:6], 'little'),rssi=list(p[10:13]),
            noise=int.from_bytes(p[13:14], 'little', signed=True),agc=p[14],
            perm=perm,rate=int.from_bytes(p[18:20], 'little')))
    if not values:
        raise ValueError('No Intel beamforming records')
    return np.asarray(values), metadata


def fingerprint(c):
    # Canonical integer bytes avoid signed-zero differences in MATLAB storage.
    parts = np.stack((c.real,c.imag), axis=-1)
    if not np.isfinite(parts).all() or np.any(parts != np.rint(parts)) or np.any(np.abs(parts)>128):
        return None
    return parts.astype('<i2').tobytes()


def audit(raw_root, repo, output):
    names = (repo/'data/wifipose/train_data/train_data_list.txt').read_text(encoding='utf-8-sig').splitlines()
    groups = defaultdict(list)
    for name in names:
        if name.strip():groups[name.split('_')[0]].append(name.strip())
    sessions = {}
    for group, members in sorted(groups.items()):
        session = sorted({'_'.join(x.split('_')[:2]) for x in members})[0]
        same = sorted((x for x in members if x.startswith(session+'_')),key=lambda x:int(x.split('_')[-1]))
        sessions[session] = [same[i] for i in (0,len(same)//2,len(same)-1)]
    report = []
    matched_metadata = []
    decoded = 0
    for session, selected in sessions.items():
        mats = {n:load_mat(repo/'data/wifipose/train_data/csi'/(n+'.mat')) for n in selected}
        for node in range(3):
            path = raw_root/f'r{node+1}'/'data'/(session+'.dat')
            csi, meta = read_intel(path)
            decoded += len(csi)
            index = defaultdict(list)
            for i,c in enumerate(csi):index[fingerprint(c)].append(i)
            for name,mat in mats.items():
                found = [index.get(fingerprint(mat[node,:,:,t]),[]) for t in range(20)]
                unique = all(len(x)==1 for x in found)
                ids = [x[0] for x in found] if unique else []
                exact = unique and np.array_equal(csi[ids].transpose(1,2,0),mat[node])
                report.append(dict(sample=name,node=node,raw=str(path),decoded_packets=len(csi),
                    uniquely_matched_frames=sum(len(x)==1 for x in found),raw_packet_indices=ids,
                    all_complex_values_exact=bool(exact),
                    chronological=bool(ids and np.all(np.diff(ids)>0)),
                    integer_component_scale_unchanged=bool(exact)))
                if exact:matched_metadata.extend(meta[i] for i in ids)
            print(json.dumps(dict(session=session,receiver=node+1,decoded=len(csi),
                exact_windows=sum(r['all_complex_values_exact'] for r in report[-len(selected):]))),flush=True)
    result = dict(offline_only=True,raw_root=str(raw_root),training_split_only=True,
        selection='First available capture session in each of nine training groups; first/middle/last listed window in that session; all three receivers',
        sessions=list(sessions),mat_windows=sum(map(len,sessions.values())),node_windows=len(report),
        decoded_raw_packets=decoded,matched_node_frames=len(matched_metadata),
        all_selected_windows_exact=all(r['all_complex_values_exact'] and r['chronological'] for r in report),
        receiver_axis='MAT node0/1/2 matches raw r1/r2/r3 respectively',
        carrier_order='Unchanged sequential Intel decoder order; RX-chain perm applied separately',
        amplitude='Exactly raw signed-int8 CSI components stored as doubles; no nontrivial RSSI/AGC scaling in matched MAT values',
        metadata=dict(agc_counts=dict(Counter(x['agc'] for x in matched_metadata)),
            noise_counts=dict(Counter(x['noise'] for x in matched_metadata)),
            rate_counts=dict(Counter(x['rate'] for x in matched_metadata)),
            rx_permutation_counts=dict(Counter(str(x['perm']) for x in matched_metadata))),
        matches=report,
        limitations=['Representative exact matches, not an exhaustive check of all published MAT files.',
            'Raw logs expose Intel RSSI/AGC but do not calibrate Nexmon hardware gain or different propagation paths.',
            'Absolute signed-frequency mapping uses the Intel HT20/Ng2 specification in addition to this storage-order audit.'],
        sources=['https://raw.githubusercontent.com/dhalperi/linux-80211n-csitool-supplementary/master/matlab/read_bfee.c',
            'https://raw.githubusercontent.com/dhalperi/linux-80211n-csitool-supplementary/master/matlab/read_bf_file.m'])
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    if not result['all_selected_windows_exact']:
        raise ValueError('Reference correspondence incomplete; raw result retained')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--raw-root',type=Path,required=True);p.add_argument('--repo',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=audit(a.raw_root,a.repo,a.output)
    print(json.dumps({k:r[k] for k in ('mat_windows','node_windows','decoded_raw_packets','matched_node_frames','all_selected_windows_exact')}))
