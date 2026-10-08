"""Prepare isolated network-adapter gate from reviewed resident capture bytes."""
import argparse,hashlib,json,re,shutil
from pathlib import Path

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    root=Path(__file__).resolve().parents[2];base=root/'tools/pose-v1/evidence/resident-20261008-r6'
    complete=json.loads((base/'completion-review.json').read_text());assert complete
    build=json.loads((a.build/'build-result.json').read_text(encoding='utf-8-sig'))
    for rel,digest in build['sources'].items():assert sha(root/rel)==digest==sha(a.build/Path(rel).name)
    for name,digest in build['programs'].items():assert sha(a.build/name)==digest
    assert 'error:' not in (a.build/'build.log').read_text() and 'warning:' not in (a.build/'build.log').read_text()
    assert not a.output.exists();a.output.mkdir(parents=True)
    stage=base/'resident-three/results';data=(stage/'encoder/video.h264').read_bytes()
    packets=[json.loads(r) for r in (stage/'packets.jsonl').read_text().splitlines()]
    assert sum(r['bytes'] for r in packets)==len(data)
    offset=0;frames=[];params=[]
    for packet in packets:
        chunk=data[offset:offset+packet['bytes']];offset+=len(chunk)
        starts=list(re.finditer(b'\x00\x00(?:\x00)?\x01',chunk))
        assert not chunk or starts and starts[0].start()==0
        for i,start in enumerate(starts):
            end=starts[i+1].start() if i+1<len(starts) else len(chunk);nal=chunk[start.end():end];typ=nal[0]&31
            assert not nal[0]&128 and typ in (1,5,7,8)
            if typ in (7,8):
                if len(params)<2:params.append(nal.hex())
                else:assert nal.hex()==params[typ-7]
            else:
                assert len(starts)==1 and nal[1]&128
                frames.append(dict(encoded_id=len(frames),pts_us=packet['pts_us'],vcl_sha256=hashlib.sha256(nal).hexdigest(),idr=typ==5))
    assert len(frames)==493 and frames[0]['idr'] and len(params)==2
    assert len({r['vcl_sha256'] for r in frames if r['idr']})==sum(r['idr'] for r in frames)
    (a.output/'video.h264').write_bytes(data)
    (a.output/'packets.tsv').write_bytes(''.join(f"{r['pts_us']}\t{r['bytes']}\n" for r in packets).encode())
    (a.output/'expected.json').write_bytes((json.dumps(dict(parameters=params,frames=frames,scope='recorded_resident_packets_only'),indent=2)+'\n').encode())
    for name in build['programs']:shutil.copyfile(a.build/name,a.output/name)
    for name in ['board_application_preflight.py','run-owned-rtsp.sh']:shutil.copyfile(root/'tools/pose-v1'/name,a.output/name)
    shutil.copyfile(base/'resident-three/preflight.json',a.output/'baseline-preflight.json')
    manifest=dict(scope='CPU_owned_AU_network_adapter_gate_no_new_VPU_NPU_HDMI',frames=493,programs=build['programs'],sources=build['sources'],builder_sha256=build['builder_sha256'],vendor_manifest_sha256=sha(a.build/'vendor-files.json'),capture_sha256=sha(a.output/'video.h264'),preparer_sha256=sha(Path(__file__)))
    (a.output/'manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
    (a.output/'files.sha256').write_bytes(''.join(sha(f)+'  '+f.name+'\n' for f in sorted(a.output.iterdir()) if f.name!='files.sha256').encode())
    print(json.dumps({'payloads':len(list(a.output.iterdir()))-1,'manifest_sha256':sha(a.output/'manifest.json'),'frames':493}))
if __name__=='__main__':main()
