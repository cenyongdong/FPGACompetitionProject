"""Package the already reviewed finite VPU output and strict single-slice index."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from audit_vpu_annexb import inspect

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--build',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    root=Path(__file__).resolve().parents[2]
    stage=root/'tools/pose-v1/evidence/video-descriptor-20261007-r5/encode'
    data=(stage/'results/video.h264').read_bytes()
    assert hashlib.sha256(data).hexdigest()=='d51c98b183b4b0ff5ff7142403c1fa1c8146a5be4be71672afcd17e9d38eaac3'
    reviewed=json.loads((stage.parent/'completion-review.json').read_text())
    assert reviewed['repeat_h264_byte_identical'] and reviewed['host_review']['all_frame_ids_correct']
    nals=inspect(stage)
    rows=[];covered=0;frames=0
    for chunk in nals['chunks']:
        group=[n for n in nals['nals'] if chunk['offset']<=n['offset']<chunk['offset']+chunk['bytes']]
        for n in group:
            assert n['offset']==covered and n['start_code_bytes']==4
            kind={7:'SPS',8:'PPS',5:'FRAME',1:'FRAME'}[n['type']]
            if kind=='FRAME':
                assert len(group)==1 and chunk['pts_us']==frames*100000
                assert data[n['offset']+5]&0x80, 'first_mb_in_slice must be zero'
                frames+=1
            rows.append(f"{kind}\t{chunk['pts_us']}\t{n['offset']}\t{n['end']-n['offset']}\t{n['type']}\n")
            covered=n['end']
    assert covered==len(data) and frames==54
    program=a.build/'pose_rtsp_replay_check';source=root/'software/pose_v1/src/rtsp_replay_check.cpp'
    assert sha(source)==sha(a.build/source.name)
    binary=program.read_bytes()
    assert binary[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<H',binary,18)[0]==183
    buildlog=(a.build/'build.log').read_text()
    assert not any(s in buildlog for s in ('warning:','error:','libicraft','RPATH','RUNPATH'))
    assert not a.output.exists();a.output.mkdir(parents=True)
    for src,name in [(stage/'results/video.h264','video.h264'),(program,program.name),
                     (root/'tools/pose-v1/board_application_preflight.py','board_application_preflight.py'),
                     (root/'tools/pose-v1/run-rtsp-replay.sh','run-rtsp-replay.sh')]:
        (a.output/name).write_bytes(src.read_bytes())
    (a.output/'index.tsv').write_bytes(''.join(rows).encode())
    manifest={'scope':'finite_RTSP_replay_no_VPU_NPU_HDMI','frames':54,'fps':10,'maximum_seconds':60,
              'h264_sha256':sha(stage/'results/video.h264'),
              'program_sha256':sha(program),'source_sha256':sha(source),'vendor_manifest_sha256':sha(a.build/'vendor-files.json'),
              'source_origin':'video-descriptor-20261007-r5; actual capture PTS; prerecorded discrete windows',
              'nal_contract':'one first_mb=0 VCL NAL per timestamp; reject unsupported layout',
              'nal_type_counts':nals['nal_type_counts']}
    (a.output/'manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
    payloads=sorted(a.output.iterdir())
    (a.output/'files.sha256').write_bytes(''.join(f'{sha(f)}  {f.name}\n' for f in payloads).encode())
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()
