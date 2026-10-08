"""Freeze a bounded 103-window schedule; does not connect or execute a model."""
import argparse,hashlib,json,struct
from pathlib import Path
import mixed_validation_gate as old

def main():
    p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    old.verify(a.package);catalog=[line.split()[1] for line in (a.package/'cases.tsv').read_text().splitlines() if line.startswith('expanded\t') or line.startswith('expanded ')]
    assert len(catalog)==27 and len(set(catalog))==27
    def source(sequence):
        if not 0<=sequence<103:raise ValueError('Bounded transport sequence outside 0..102')
        return catalog[sequence%27]
    rejected=0
    for value in (-1,103,104):
        try:source(value)
        except ValueError:rejected+=1
        else:raise AssertionError('Out-of-range accepted')
    assert source(0)==catalog[0] and source(102)==catalog[21] and rejected==3
    frames=[]
    for i in range(103):
        case=source(i);original=(a.package/'inputs'/(case+'.csi')).read_bytes();raw=bytearray(original);struct.pack_into('<Q',raw,16,100000+i)
        assert bytes(raw[:16]+raw[24:])==original[:16]+original[24:]
        frames.append(dict(sequence=i,case=case,transport_id=100000+i,warmup=i<3,send_offset_ns=i*200000000,wire_sha256=hashlib.sha256(raw).hexdigest(),payload_sha256=hashlib.sha256(raw[32:]).hexdigest()))
    report=dict(status='schedule_prepared_not_executed',package_manifest_sha256=old.sha(a.package/'manifest.json'),frames=frames,expected_send_duration_seconds=20.4,warmups=3,measured=100,request_limit=103,record_limit=103,encoder_ready_seconds=30,encoder_frame_limit=1000,network_seconds=100,client_seconds=105,outer_seconds=180,boundary_rejections=rejected,hardware_executed=False,implementation_of_long_entry_pending=True)
    a.output.write_text(json.dumps(report,indent=2)+'\n');print('103 fixed input identities prepared; no hardware execution.')
if __name__=='__main__':main()
