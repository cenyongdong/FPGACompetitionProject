"""Audit training MAT layout/order evidence and fit a bounded empirical scale.

Uses only the existing training split for reference fitting/holdout. Receiver
fit uses only the first-second startup prefix, never later evaluation windows.
No inference, hardware connection, model or board protocol changes.
"""
import argparse
from collections import defaultdict,Counter
import json
from pathlib import Path
import sys

import h5py
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'software/core/input'))
from csi_io import load_mat
from diagnose_metadata import packets
from csi_verify import parse_payload
from map_node_windows import HT20_NG2
from native_carriers import select_packed,decode_selected
from single_node_adapter import SingleNodeAdapter,packet_rms
from validate_dedup import read_events,clock_segments,select_first_valid,stats


def reference_selection(data,per_group=16):
    names=(data/'train_data_list.txt').read_text(encoding='utf-8-sig').splitlines()
    groups=defaultdict(list)
    for name in names:
        if name.strip():groups[name.split('_')[0]].append(name.strip())
    fit,hold=[],[]
    for group,members in sorted(groups.items()):
        # Nonoverlapping first/last thirds of each file-list group; evenly spaced.
        # Never use the published test split or select by resulting scale.
        third=len(members)//3
        if third<per_group*20:
            raise ValueError('Insufficient spacing for independent reference subsets')
        for dest,start in ((fit,0),(hold,len(members)-third)):
            dest.extend(data/'csi'/(members[start+i*(third-1)//(per_group-1)]+'.mat') for i in range(per_group))
    return fit,hold,dict((g,len(v)) for g,v in groups.items())


def reference_stats(paths):
    rms,step_ratios,node_chain_rms=[],[],[]
    total=integers=0;minimum=np.inf;maximum=-np.inf
    attributes=set();shapes=set();keys=set()
    for path in paths:
        with h5py.File(path) as h:
            keys.update(h.keys());attributes.update(h['csi_out'].attrs.keys());shapes.add(h['csi_out'].shape)
        c=load_mat(path)
        if not np.isfinite(c).all():raise ValueError('Non-finite training sample')
        parts=np.concatenate((c.real.reshape(-1),c.imag.reshape(-1)))
        integers+=int(np.sum(parts==np.rint(parts)));total+=parts.size
        minimum=min(minimum,float(parts.min()));maximum=max(maximum,float(parts.max()))
        rms.extend(packet_rms(c).reshape(-1).tolist())
        node_chain_rms.extend(np.sqrt(np.mean(np.abs(c)**2,axis=(2,3))).tolist())
        # Phase-gap diagnostic: half-spacing at slots13/28 supports HT20 Ng2.
        # It cannot determine absolute frequency direction or replace metadata.
        delta=np.abs(np.angle(c[:,:,1:,:]*np.conj(c[:,:,:-1,:])))
        strength=np.minimum(np.abs(c[:,:,1:,:]),np.abs(c[:,:,:-1,:]))>5
        normal=np.delete(np.arange(29),[13,28])
        normal_delta=np.where(strength[:,:,normal,:],delta[:,:,normal,:],np.nan).transpose(0,1,3,2)
        usable=np.any(np.isfinite(normal_delta),axis=-1)
        typical=np.full(usable.shape,np.nan)
        typical[usable]=np.nanmedian(normal_delta[usable],axis=-1)
        valid=(typical>.15)&(typical<2.5)
        ratios=delta/np.where(valid,typical,np.nan)[:,:,None,:]
        step_ratios.append(np.where(strength,ratios,np.nan).transpose(0,1,3,2).reshape(-1,29))
    gaps=np.concatenate(step_ratios)
    return dict(windows=len(paths),node_packet_rms=stats(rms),
        integer_component_fraction=integers/total,component_min=minimum,component_max=maximum,
        hdf_keys=sorted(keys),hdf_shapes=[list(s) for s in sorted(shapes)],hdf_csi_attributes=sorted(attributes),
        node_chain_window_rms=stats(np.asarray(node_chain_rms).reshape(-1)),
        adjacent_phase_gap_median_ratio=np.nanmedian(gaps,axis=0).tolist()),np.asarray(rms)


def audit(repo,capture,output,raw_audit=None):
    output.mkdir(parents=True,exist_ok=True)
    binding=json.loads(raw_audit.read_text(encoding='utf-8')) if raw_audit else None
    if binding and not binding['all_selected_windows_exact']:
        raise ValueError('Raw-log reference audit failed')
    fit_paths,held_paths,groups=reference_selection(repo/'data/wifipose/train_data')
    fit,reference_rms=reference_stats(fit_paths)
    held,held_rms=reference_stats(held_paths)
    events,_=read_events(capture/'capture.pcap');clock_segments(events);kept=select_first_valid(events)
    raw_summary=json.loads((capture/'summary.json').read_text())
    lock=next(x for x in raw_summary['startup'] if x['locked'])
    prefix=[e for e in kept if e.segment==lock['segment'] and e.time_us<=lock['calibration_end_us']]
    if len(prefix)!=lock['observations']:
        raise ValueError('Amplitude prefix differs from causal time calibration prefix')
    prefix_csi=np.asarray([decode_selected(select_packed(e.words,HT20_NG2,e.original_words)) for e in prefix])
    source_rms=np.sqrt(np.mean(np.abs(prefix_csi)**2,axis=(1,2)))
    if not np.isfinite(source_rms).all() or np.any(source_rms<=0):
        raise ValueError('Invalid source amplitude prefix')
    gain=float(np.median(reference_rms)/np.median(source_rms))
    identity={(e.meta['mac'],e.meta['channel']) for e in kept}
    if len(identity)!=1:raise ValueError('Receiver source changed')
    mac,channel=identity.pop()
    profile=dict(schema=1,method='fixed_shared_empirical_gain',gain=gain,
        receiver_nodes=1,receiver_label='RT-AC86U-sample-1',transmitter_mac=mac,chanspec=channel,
        signed_carriers=HT20_NG2,target_hz=300,bandwidth_mhz=20,
        target='Median per-node/per-packet RMS pooled over chains/carriers of balanced training-only samples',
        source_fit=dict(segment=int(lock['segment']),end_us=int(lock['calibration_end_us']),events=len(prefix)),
        reference_fit_windows=len(fit_paths),physical_power_calibrated=False,
        reference_holdout_packet_rms_median=float(np.median(held_rms)),
        pose_accuracy_validated=False,training_order_binding_verified=bool(binding),model_ready=False,
        training_binding_scope=dict(node_windows=binding['node_windows'],mat_windows=binding['mat_windows'],
            audit=raw_audit.name) if binding else None,
        limitations=['Empirical numeric-scale alignment only; no calibrated RF power units or causal device-gain identification.',
            'One fixed shared scalar; no per-frame/chain/carrier normalization, integer rounding or clipping.',
            'Valid only as this receiver/setup candidate; do not silently reuse on another node or channel.'])
    (output/'amplitude-profile.json').write_text(json.dumps(profile,indent=2),encoding='utf-8')
    adapter=SingleNodeAdapter(profile)
    with np.load(capture/'native30/single-node-windows.npz') as z:
        original=z['csi_uncalibrated'];ids=z['original_event_indices'];signed=z['signed_subcarriers']
    if tuple(signed)!=HT20_NG2 or any(int(i)<=prefix[-1].index for i in ids.reshape(-1)):
        raise ValueError('Amplitude evaluation overlaps its calibration prefix or carrier profile changed')
    calibrated=adapter.apply(original)
    before=packet_rms(original).reshape(-1);after=packet_rms(calibrated).reshape(-1)
    def alignment(values):
        return dict(rms=stats(values),median_ratio_to_reference_holdout=float(np.median(values)/np.median(held_rms)),
            log_median_offset_db=float(20*np.log10(np.median(values)/np.median(held_rms))),
            fraction_inside_reference_holdout_01_99=float(np.mean((values>=np.quantile(held_rms,.01))&(values<=np.quantile(held_rms,.99)))))
    phase_delta=np.angle(calibrated*np.conj(original))
    np.savez_compressed(output/'adapted-node-windows.npz',csi_empirical=calibrated,
        original_event_indices=ids,signed_subcarriers=signed,gain=np.asarray(gain))
    rssis=Counter()
    for _,port,p in packets(capture/'capture.pcap'):
        if port==5500:rssis[parse_payload(p,64)['rssi']]+=1
    result=dict(offline_only=True,hardware_connected=False,model_ready=False,
        model_preprocessing_math_and_board_protocol_changed=False,
        reference=dict(groups=groups,fit=fit,holdout=held,
            fit_files=[str(p.relative_to(repo)) for p in fit_paths],holdout_files=[str(p.relative_to(repo)) for p in held_paths],
            published_test_split_used_for_fitting=False),
        order=dict(physical_profile=list(HT20_NG2),loader='csi_out real/imag + transpose(3,2,1,0); no carrier permutation in model loader',
            numerical_half_gap_positions=[13,28],
            matching_order_evidence='Exact complex-value correspondence with original Intel records after RX permutation' if binding else
                'Integer-like raw CSI and phase-gap pattern plus Intel decoder table; original MAT-export script absent',
            exact_training_export_binding_proven=bool(binding),
            verification_scope=dict(audit=raw_audit.name,node_windows=binding['node_windows'],
                mat_windows=binding['mat_windows'],exhaustive=False) if binding else None),
        amplitude=dict(profile='amplitude-profile.json',gain=gain,source_fit=stats(source_rms),
            reference_fit_median=float(np.median(reference_rms)),source_fit_median=float(np.median(source_rms)),
            evaluation_windows=len(original),before=alignment(before),after=alignment(after),
            maximum_phase_delta_rad=float(np.max(np.abs(phase_delta))),
            source_header_rssi_counts=dict(rssis),
            absolute_calibration_blockers=[('Matched training MAT retains raw quantized CSI, not RSSI/AGC-scaled physical values; raw metadata is available.' if binding else
                'Training MAT has only csi_out, no per-frame RSSI/AGC/noise or original Intel log.'),
                'Nexmon last_rssi/PHY status are copied from the normal RX path, without same-event calibration proof.',
                'Unpaired rooms/devices/positions make fixed hardware gain and propagation differences unidentifiable.']),
        sources=['https://dhalperi.github.io/linux-80211n-csitool/faq.html',
            'https://raw.githubusercontent.com/dhalperi/linux-80211n-csitool-supplementary/master/matlab/read_bfee.c',
            'https://raw.githubusercontent.com/dhalperi/linux-80211n-csitool-supplementary/master/matlab/get_scaled_csi.m',
            'https://github.com/citysu/csiread/blob/master/csiread/utils.py'])
    (output/'summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,required=True);p.add_argument('--capture',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--raw-audit',type=Path,help='Completed original Intel raw-log/MAT correspondence report')
    a=p.parse_args();r=audit(a.repo,a.capture,a.output,a.raw_audit)
    print(json.dumps(dict(order=r['order'],amplitude=r['amplitude']),indent=2))
