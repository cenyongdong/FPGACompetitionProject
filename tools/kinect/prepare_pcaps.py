"""Prepare unchanged native CSI windows/features from PC-collected real streams.

Only a common PC receipt interval is retained for replay scheduling. Original
captures stay intact. RF alignment still uses the existing native same-event
decoder; receipt times are never used to invent RF sample identities.
"""
import argparse
import json
from pathlib import Path
import struct
import subprocess

ROLES=('rx1','rx2','rx3')
TX_MAC='f0:2f:74:39:45:6c'
GAINS=(7.114209668296235,2.047225813311503,9.11067064816795)


def load(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def save(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def source_identity(packet):
    if len(packet)<42 or packet[12:14]!=b'\x08\x00':return None
    ihl=(packet[14]&15)*4
    if packet[23]!=17:return None
    udp=14+ihl
    port=struct.unpack_from('>H',packet,udp+2)[0];payload=packet[udp+8:]
    if port==5500 and len(payload)==274 and payload[:2]==b'\x11\x11':return payload[4:10].hex(':'),struct.unpack_from('<H',payload,14)[0]
    if port==5501 and len(payload)==50 and payload[:4]==b'NMD3':return payload[8:14].hex(':'),struct.unpack_from('<H',payload,18)[0]
    return None


def prepare(raw,output,replay,preprocess):
    raw=Path(raw);output=Path(output);metadata=load(raw/'metadata.json');result=load(raw/'result.json')
    if not result['all_three_received'] or metadata.get('simulation'):raise ValueError('Three actual independent RX captures required')
    frequency=metadata['qpc_frequency_hz'];streams={};ranges={}
    for role in ROLES:
        segments=[s for s in result['segments'] if s['name'].startswith(role+'-') and s['complete_packets']]
        # Each finite training clip uses one continuous connection per receiver.
        if len(segments)!=1:raise ValueError('Select one common continuous connection segment per RX before preparing this clip')
        name=segments[0]['name'];rows=[json.loads(line) for line in (raw/(name+'-timing.jsonl')).open()]
        streams[role]=(raw/(name+'.pcap'),rows);ranges[role]=(rows[0]['host_recv_end_qpc'],rows[-1]['host_recv_end_qpc'])
    lo=max(v[0] for v in ranges.values())+frequency
    hi=min(v[1] for v in ranges.values())-frequency//5
    if hi<=lo:raise ValueError('No usable common receipt interval')
    output.mkdir(exist_ok=False);identities=set();timing={};counts={}
    for role,(source,rows) in streams.items():
        selected=[r for r in rows if lo<=r['host_recv_end_qpc']<=hi];counts[role]=len(selected)
        with source.open('rb') as original,(output/(role+'.pcap')).open('xb') as target:
            target.write(original.read(24))
            for row in selected:
                original.seek(row['pcap_offset']);record=original.read(row['record_bytes'])
                if len(record)!=row['record_bytes']:raise ValueError('Original PCAP changed')
                target.write(record)
                identity=source_identity(record[16:])
                if identity:identities.add(identity)
                if role=='rx1':timing.setdefault(row['capture_ns'],row)
    if len(identities)!=1 or next(iter(identities))[0]!=TX_MAC:raise ValueError('Transmitter/channel identity differs across RX')
    mac,channel=next(iter(identities))
    command=[str(Path(replay).resolve()),'--source-mac',mac,'--channel',hex(channel),'--gains',*map(str,GAINS),
        '--pcaps',*[str((output/(r+'.pcap')).resolve()) for r in ROLES],
        '--max-sequence-skew','0','--max-skew-us','5000','--report',str((output/'replay.json').resolve()),
        '--ledger',str((output/'replay.jsonl').resolve()),'--output',str((output/'windows.piwcsi2').resolve())]
    run=subprocess.run(command,capture_output=True,text=True)
    (output/'replay-native.log').write_text(run.stdout+run.stderr)
    if run.returncode:raise RuntimeError('Native replay failed; inspect preserved native log')
    features=subprocess.run([str(Path(preprocess).resolve()),str((output/'windows.piwcsi2').resolve()),str((output/'tokens.f32').resolve())],capture_output=True,text=True)
    (output/'preprocess-native.log').write_text(features.stdout+features.stderr)
    if features.returncode:raise RuntimeError('Original native preprocessing failed')
    count=0;missing=0
    with (output/'windows.piwcsi2').open('rb') as source,(output/'windows.jsonl').open('x') as ledger:
        while True:
            record=source.read(86432)
            if not record:break
            if len(record)!=86432:raise ValueError('Truncated native window')
            frame,source_ns=struct.unpack_from('<QQ',record,16);receipt=timing.get(source_ns)
            if receipt is None:missing+=1
            ledger.write(json.dumps(dict(record=count,frame=str(frame),source_ns=str(source_ns),valid=receipt is not None,
                host_window_end_receipt_qpc=receipt['host_recv_end_qpc'] if receipt else None,
                label_time_is_receipt_not_RF=True))+'\n');count+=1
    native=load(output/'replay.json')
    report=dict(schema='KINECT-CSI-DIRECT1',windows=count,missing_window_receipts=missing,qpc_frequency_hz=frequency,
        transmitter_mac=mac,chanspec=channel,gains=GAINS,retained_packets=counts,
        common_receipt_start_qpc=lo,common_receipt_end_qpc=hi,common_receipt_seconds=(hi-lo)/frequency,
        source=str(raw.resolve()),board_used=False,model_inference=False,simulation=False,
        original_preprocess=True,RF_sample_association='native same RF sequence only; no cross-node interpolation',
        RF_clock_synchronized=False,native_replay=native)
    save(output/'metadata.json',report);return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--raw',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--replay',required=True,type=Path);p.add_argument('--preprocess',required=True,type=Path)
    a=p.parse_args();print(json.dumps(prepare(a.raw,a.output,a.replay,a.preprocess),indent=2))
