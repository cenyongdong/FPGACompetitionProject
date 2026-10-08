"""Independent sender/receiver/result mapping, not a source of model data."""
import argparse,hashlib,json,struct
from pathlib import Path
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True);p.add_argument('--results',type=Path,required=True);p.add_argument('--client',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    sender=load(a.client/'sender.json');ingress=rows(a.results/'tcp-input/received.jsonl');calls=rows(a.results/'inference.jsonl')
    assert sender['status']=='raw_stream_plus_repeat_sent_no_receiver_ack' and sender['fps']==2 and sender['startup_wait_only']
    assert not (a.client/'sender.stderr.log').read_bytes()
    provenance=load(a.client/'controller-sources.json')
    assert set(provenance)=={'tcp_live_peer_ready.py','send_live_windows_ready.py'}
    assert all(digest==sha(Path(__file__).with_name(name)) for name,digest in provenance.items())
    assert len(ingress)==len(sender['sent'])==len(calls) in (4,28)
    for i,(sent,got,result) in enumerate(zip(sender['sent'],ingress,calls)):
        raw=a.package/'inputs'/(result['case']+'.csi');header=raw.read_bytes()[:32]
        assert sent['case']==result['case'] and sent['sha256']==sha(raw) and sent['bytes']==raw.stat().st_size==86432
        assert sent['session']==got['session']==(2 if i==len(calls)-1 else 1)
        assert sent['frame_id']==got['frame_id']==result['frame_id']==struct.unpack_from('<Q',header,16)[0]
        assert got['source_time_ns']==struct.unpack_from('<Q',header,24)[0] and got['sequence']==got['call']==result['call']==i
    assert calls[0]['case']==calls[-1]['case'] and sender['sent'][0]['sha256']==sender['sent'][-1]['sha256']
    assert all(x['arrived_ns']<y['arrived_ns'] for x,y in zip(ingress,ingress[1:]))
    assert load(a.results/'tcp-input/summary.json')==dict(sessions=2,received=len(calls),consumed=len(calls),rejected=0,overwritten=0,reconnect_discarded=0)
    report=dict(status='complete_CSI_sender_receiver_result_mapping_verified',windows=len(calls),raw_bytes=sum(x['bytes'] for x in sender['sent']),sessions=2,repeat_original_bytes=True,loss_or_rejection=0,reference_used_only_as_oracle=True,sender_sha256=sha(a.client/'sender.json'),receiver_log_sha256=sha(a.results/'tcp-input/received.jsonl'),controller_sources=provenance)
    a.output.write_bytes((json.dumps(report,indent=2)+'\n').encode());print(json.dumps(report,indent=2))
if __name__=='__main__':main()
