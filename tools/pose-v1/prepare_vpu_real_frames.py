"""54-frame finite sequence from27 verified ARM renderer outputs."""
from pathlib import Path
import argparse,hashlib,json,shutil
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'tools/pose-v1/evidence/render-20261007-r1/cpu-render'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);a.add_argument('--build',type=Path,required=True);args=a.parse_args()
    assert not args.output.exists()
    declared={}
    for line in (SOURCE/'files.sha256').read_text().splitlines():
        h,name=line.split('  ',1);declared[name.lstrip('./')]=h
    manifest= json.loads((ROOT/'.local/pose-v1-render/package-20261007-r1/manifest.json').read_text())
    cases=manifest['expanded_cases'];assert len(cases)==27
    source_records=[]
    for i,case in enumerate(cases):
        p=SOURCE/f'frames/call{i}.nv12';m=SOURCE/f'frames/call{i}.json'
        assert sha(p)==declared[f'frames/call{i}.nv12'] and sha(m)==declared[f'frames/call{i}.json']
        record=json.loads(m.read_text());assert record['frame_id']==case['frame_id'] and len(record['projected'])==14
        assert p.stat().st_size==1280*720*3//2
        source_records.append({'source_index':i,'source_case':case['case'],'source_group':case['group'],'source_frame_id':case['frame_id'],
                               'source_nv12_sha256':sha(p),'source_metadata_sha256':sha(m),'projected':record['projected'],'top_index':record['top_index']})
    assert len({r['source_nv12_sha256'] for r in source_records})==27
    args.output.mkdir(parents=True)
    records=[]
    with (args.output/'frames.nv12').open('xb') as f:
        for i in range(54):
            source=i//2;base=np.frombuffer((SOURCE/f'frames/call{source}.nv12').read_bytes(),dtype=np.uint8).copy()
            y=base[:1280*720].reshape(720,1280);uv=base[1280*720:].reshape(360,1280)
            y[600:680,40:1240]=16;uv[300:340,40:1240]=128
            # Six-bit encoding ID and moving stripe; all diagnostic overlays
            # are below the selected actual skeleton, never alter its joints.
            for bit in range(6):y[600:632,40+bit*64:88+bit*64]=235 if i&(1<<bit) else 16
            x=40+i*21;y[640:680,x:x+24]=235
            data=base.tobytes();f.write(data)
            records.append({'encoded_frame_id':i,'source_index':source,'source_frame_id':cases[source]['frame_id'],'source_case':cases[source]['case'],
                            'repeated_source':bool(i%2),'pts_us':i*100000,'marker_x':x,'sha256':hashlib.sha256(data).hexdigest()})
    # Include producer source identities; build must match current bytes.
    sources={}
    for sub in ('src/vpu_encoder.cpp','src/vpu_sequence_check.cpp','include/vpu_encoder.hpp'):
        p=ROOT/'software/pose_v1'/sub;copy=args.build/p.name;assert p.read_bytes()==copy.read_bytes();sources[sub]=sha(p)
    program=args.build/'pose_vpu_sequence_check';b=program.read_bytes();assert b[:4]==b'\x7fELF' and int.from_bytes(b[18:20],'little')==183
    shutil.copyfile(program,args.output/program.name)
    for name in ('board_application_preflight.py','run-vpu-sequence-stage.sh','hdmi_readonly_audit.py'):
        shutil.copyfile(ROOT/'tools/pose-v1'/name,args.output/name)
    result={'scope':'real_prerecorded_discrete_skeletons_no_new_inference','width':1280,'height':720,'fps':10,'frames':54,'sources':27,
            'source_hold_frames':2,'format':'NV12','input_sha256':sha(args.output/'frames.nv12'),'program_sha256':sha(program),
            'source_files':sources,'source_records':source_records,'frame_records':records,'diagnostic_overlay':[40,600,1240,680],
            'HDMI_initialized':False,'NPU_initialized':False,'colorimetry':'601 limited transfer709'}
    (args.output/'manifest.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
    (args.output/'files.sha256').write_bytes(''.join(f'{sha(p)}  {p.name}\n' for p in sorted(args.output.iterdir()) if p.name!='files.sha256').encode())
    print('Verified27 actual ARM frames; generated54 inputs',args.output)

if __name__=='__main__':main()
