"""Bounded ordered router-PCAP TCP input, processed during acquisition.

The router streams original Ethernet PCAP through existing BusyBox nc. Only
one explicitly expected LAN router may connect; no model or board output.
"""
import argparse
import json
from pathlib import Path
import socket
import time

import numpy as np

from diagnose_metadata import packets_stream, decode
from native_carriers import decode_selected
from stream_node import NodeStream
from validate_dedup import stats
from single_node_adapter import SingleNodeAdapter


class RecordingReader:
    def __init__(self,stream,output):
        self.stream,self.output,self.count=stream,output,0

    def read(self,n):
        data=self.stream.read(n)
        self.count+=len(data)
        if self.count>32*1024*1024:
            raise ValueError('Live byte budget exceeded')
        self.output.write(data)
        return data


def capture(output,source_mac,channel,bind='192.168.50.102',port=39033,amplitude_profile=None,retry_startup=False):
    output.mkdir(parents=True,exist_ok=False)
    adapter=NodeStream(source_mac,channel,retry_startup=retry_startup)
    value_adapter=SingleNodeAdapter(amplitude_profile) if amplitude_profile else None
    adapted=[]
    windows,selected,processing,original28,legacy28=[],set(),[],[],[]
    first_window=first_valid_window=None
    count=0
    with socket.socket() as server:
        server.bind((bind,port));server.listen(1);server.settimeout(30)
        print(json.dumps(dict(listening=bind,port=port)),flush=True)
        connection,peer=server.accept()
        if peer[0]!='192.168.50.1':
            connection.close();raise ValueError('Unexpected stream source')
        print(json.dumps(dict(connected_peer=peer[0],port=port)),flush=True)
        started=time.monotonic()
        connection.settimeout(25)
        with connection,connection.makefile('rb') as stream,(output/'capture.pcap').open('xb') as raw:
            reader=RecordingReader(stream,raw)
            for stamp,udp,payload in packets_stream(reader):
                count+=1
                if count>40000 or time.monotonic()-started>30:
                    raise ValueError('Live packet/time budget exceeded')
                tick=time.perf_counter_ns()
                ready=adapter.feed(stamp,udp,payload)
                processing.append((time.perf_counter_ns()-tick)/1000)
                if udp==5501:
                    d=decode(payload)
                    if 'original_words' in d:
                        original28.append(d['original_words'][0])
                elif udp==5500:
                    # Header18 + native word28. Keep source bytes in PCAP.
                    legacy28.append(int.from_bytes(payload[18+28*4:18+29*4],'little'))
                for w in ready:
                    if first_window is None:
                        first_window=time.monotonic()-started
                    if w.valid:
                        ids={o.index for o in w.observations}
                        if selected & ids:raise ValueError('Live event reused')
                        selected.update(ids)
                        if value_adapter is not None:
                            adapted.append(value_adapter.map_window(w,source_mac,channel))
                        if first_valid_window is None:
                            first_valid_window=time.monotonic()-started
                    windows.append(dict(segment=w.segment,start_slot=w.start_slot,valid=w.valid,
                        reason=w.reason,interval_gate=w.interval_gate,
                        original_event_indices=[o.index if o else -1 for o in w.observations],
                        emitted_s=time.monotonic()-started))
            total_bytes=reader.count
    elapsed=time.monotonic()-started
    if original28 and len(original28)!=len(legacy28):
        raise ValueError('NMD2 count differs from legacy CSI count')
    result=dict(live_transport=True,model_ready=False,model_or_board_protocol_changed=False,
        retry_startup=bool(retry_startup),
        elapsed_s=elapsed,packets=count,pcap_bytes=total_bytes,**adapter.finish(),
        windows=len(windows),valid_windows=sum(w['valid'] for w in windows),
        also_previous_interval_gate=sum(w['interval_gate'] for w in windows),
        first_window_emitted_s=first_window,
        first_valid_window_emitted_s=first_valid_window,
        windows_emitted_before_stream_closed=sum(w['emitted_s']<elapsed for w in windows),
        processing_us=stats(processing),native28=dict(samples=len(original28),
            original_nonzero=sum(x!=0 for x in original28),
            original_differs_from_overwritten=sum(a!=b for a,b in zip(original28,legacy28)),
            magnitude=stats(np.abs(decode_selected(np.asarray(original28,dtype='u4'))))) if original28 else None,
        limitations=['Real-time host time candidates, not model inputs or pose recognition.',
            'No absolute RF-to-host latency calibration; low16 RF time continuity guards still apply.',
            'Absolute RF amplitude calibration and three independent nodes remain missing; explicit value profile required.'])
    if value_adapter is not None:
        values=np.asarray(adapted,dtype='complex128').reshape(-1,3,30,20)
        np.savez_compressed(output/'adapted-node-windows.npz',csi_empirical=values,
            original_event_indices=np.asarray([w['original_event_indices'] for w in windows if w['valid']],dtype='i8').reshape(-1,20))
        result['empirical_adapter']=dict(windows=len(values),gain=value_adapter.gain,
            profile=str(amplitude_profile),physical_power_calibrated=False,model_ready=False)
    (output/'windows.json').write_text(json.dumps(windows,indent=2),encoding='utf-8')
    (output/'summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2),flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--source-mac',required=True)
    p.add_argument('--channel',type=lambda s:int(s,0),required=True)
    p.add_argument('--amplitude-profile',type=Path,help='Explicit empirical single-node scale profile; no model packets')
    p.add_argument('--retry-startup',action='store_true',help='Discard failed startup prefixes and retry under unchanged thresholds')
    a=p.parse_args();capture(a.output,a.source_mac,a.channel,amplitude_profile=a.amplitude_profile,retry_startup=a.retry_startup)
