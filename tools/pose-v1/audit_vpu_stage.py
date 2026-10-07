"""Verify returned finite VPU stages and exact package/BOOT/SDK identity."""
import argparse
import hashlib
import json
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    a=argparse.ArgumentParser();a.add_argument('--stage',type=Path,required=True);a.add_argument('--package',type=Path,required=True);a.add_argument('--output',type=Path,required=True);args=a.parse_args()
    p=args.stage;pkg=args.package
    for line in (pkg/'files.sha256').read_text().splitlines():
        h,name=line.split('  ',1);assert sha(pkg/name)==h
    for line in (p/'files.sha256').read_text().splitlines():
        h,name=line.split('  ',1);relative=Path(name).relative_to('run-'+('encode' if 'encode' in p.name else 'negotiate'))
        assert '..' not in relative.parts and sha(p/relative)==h
    assert int((p/'exit.txt').read_text())==0 and not (p/'stderr.log').read_bytes()
    assert (p/'dmesg.before.log').read_bytes()==(p/'dmesg.after.log').read_bytes()
    identity=json.loads((p/'preflight.json').read_text())
    assert identity['SDK_packages']==['customop arm64 3.39.0','icraft arm64 3.39.0']
    assert identity['fpga_state']=='operating'
    assert next(f['sha256'] for f in identity['boot_files'] if f['name']=='BOOT.BIN')=='ff350477e624c50d2f8180fb4b9130ec7688fbc7ca553412ed7c3dd2a68b31ef'
    expected={'libicraft_hostbackend.so':'d0fbf6c81e5b57b4a908f11aad27571b8f2e68a3ede7ba33c9a4f783ba266130',
              'libicraft_zg330backend.so':'592ad913737a6d661ab9d913ff16617c8fb6bf65cc0dc8929c6886303c498a57',
              'libicraft_xrt.so':'a29e4eee6106afae0b6aada4a07e85416ac6dfc3e74083033ae5d1411749dc96'}
    assert identity['libraries']==expected
    events=[json.loads(x) for x in (p/'results/events.jsonl').read_text().splitlines()]
    formats=[x for x in events if x['event']=='format']
    assert len(formats)==2 and formats[0]['layout']==[{'stride':1280,'size':921600},{'stride':1280,'size':460800}]
    assert all((x['width'],x['height'],x['colorspace'],x['ycbcr_enc'],x['quantization'])==(1280,720,1,1,2) for x in formats)
    final=events[-1];captures=[x for x in events if x['event']=='capture']
    if final['event']=='encoding_complete':
        assert final['queued']==final['returned']==30 and final['last'] and not final['npu'] and not final['hdmi']
        assert [x['frame'] for x in events if x['event']=='input_queued']==list(range(30))
        assert sum(x['bytes'] for x in captures)==final['bytes']==(p/'results/video.h264').stat().st_size
        assert captures[-1]['flags']&0x100000 and not any(x['flags']&0x40 for x in captures)
    else:assert final=={'event':'negotiation_complete','streamed':False}
    report={'status':'returned_VPU_stage_verified','stage':p.name,'package_sha256':sha(pkg/'files.sha256'),'program_sha256':sha(pkg/'pose_vpu_encode_check'),
            'input_sha256':sha(pkg/'frames.nv12'),'returned_files':len(list(p.rglob('*'))),'exit':0,'stderr_empty':True,'kernel_unchanged':True,
            'format_records':formats,'completion':final,'capture_chunks':len(captures),'capture_pts_us':[x['pts_us'] for x in captures]}
    assert not args.output.exists();args.output.write_bytes((json.dumps(report,indent=2)+'\n').encode());print(report['status'],report['stage'])

if __name__=='__main__':main()
