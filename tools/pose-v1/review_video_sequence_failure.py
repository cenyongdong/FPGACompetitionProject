"""Join identity/queue/partial stream and read-only HDMI evidence, no devices."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'tools/pose-v1/evidence/video-sequence-20261007-r1'
PKG=ROOT/'.local/pose-v1-vpu-sequence/package-20261007-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def verify_dir(p,prefix):
    for line in (p/'files.sha256').read_text().splitlines():
        h,name=line.split('  ',1);r=Path(name).relative_to(prefix);assert '..' not in r.parts and sha(p/r)==h
def identity(p):
    d=load(p/'preflight.json');assert d['fpga_state']=='operating' and d['SDK_packages']==['customop arm64 3.39.0','icraft arm64 3.39.0']
    assert next(f['sha256'] for f in d['boot_files'] if f['name']=='BOOT.BIN')=='ff350477e624c50d2f8180fb4b9130ec7688fbc7ca553412ed7c3dd2a68b31ef'
    return d
def main():
    dest=P/'failure-review.json';assert not dest.exists()
    for line in (PKG/'files.sha256').read_text().splitlines():
        h,name=line.split('  ',1);assert sha(PKG/name)==h
    m=load(PKG/'manifest.json')
    build=ROOT/'.local/pose-v1-build/vpu-sequence-20261007-r1'
    assert sha(build/'pose_vpu_sequence_check')==m['program_sha256']
    for source,h in m['source_files'].items():
        assert sha(ROOT/'software/pose_v1'/source)==h and sha(build/Path(source).name)==h
    n=P/'negotiate';e=P/'encode';hdmi=P/'hdmi-audit';f=P/'failure-metadata'
    for p,prefix in ((n,'run-negotiate'),(e,'run-encode'),(hdmi,'hdmi-audit'),(f,'failure-metadata')):verify_dir(p,prefix)
    ids=[identity(p) for p in (n,e,hdmi)];post=load(f/'post-failure-preflight.json')
    assert all(d['boot_files']==post['boot_files'] and d['libraries']==post['libraries'] for d in ids)
    assert int((n/'exit.txt').read_text())==0 and not (n/'stderr.log').read_bytes()
    assert (n/'dmesg.before.log').read_bytes()==(n/'dmesg.after.log').read_bytes()
    assert int((e/'exit.txt').read_text())==1 and (e/'stderr.log').read_text().strip()=='poll device failure'
    before=(e/'dmesg.before.log').read_text();after=(e/'dmesg.after.log').read_text();assert after.startswith(before)
    added=after[len(before):];assert 'H264ENC: MMU ABORT' in added
    ev=[json.loads(x) for x in (e/'results/events.jsonl').read_text().splitlines()]
    queued=[x for x in ev if x['event']=='input_queued'];returned=[x for x in ev if x['event']=='input_returned'];captured=[x for x in ev if x['event']=='capture']
    assert [x['frame'] for x in queued]==list(range(9)) and returned[-1]['count']==3
    assert sum(x['bytes'] for x in captured)==(e/'results/video.h264').stat().st_size
    assert not any(x['event']=='encoding_complete' for x in ev)
    partial=load(e/'results/partial-preview/partial-review.json');assert partial['decoded_frames']==3 and [x['encoded_id'] for x in partial['frames']]==[0,1,2]
    h=load(hdmi/'inventory.json');assert not h['drm'] and not h['framebuffer_devices'] and not h['dri_devices']
    assert (hdmi/'dmesg.before.log').read_bytes()==(hdmi/'dmesg.after.log').read_bytes()
    archive=load(P/'boot-archive-review.json');vendorboot=next(x for x in archive['files'] if x['name'].lower().endswith('/boot.bin'))
    assert vendorboot['sha256']==next(x['sha256'] for x in post['boot_files'] if x['name']=='BOOT.BIN')
    result={'status':'dynamic_VPU_failed_firmware_MMU_abort_HDMI_pairing_incomplete','source_frames_verified':27,'prepared_encoded_frames':54,
            'program_sha256':m['program_sha256'],'input_sha256':m['input_sha256'],'package_sha256':sha(PKG/'files.sha256'),
            'build':'GCC9.4.0 no warnings, SDK-independent','negotiation_passed':True,'queued':len(queued),'returned':len(returned),'capture_chunks':len(captured),
            'partial_bytes':(e/'results/video.h264').stat().st_size,'partial_sha256':sha(e/'results/video.h264'),'partial_decoded_ids':[0,1,2],
            'exit':1,'stderr':'poll device failure','kernel_new_error':added.strip(),'OOM_observed':False,'completed_or_accepted':False,
            'root_cause':'not established: firmware-reported translation abort does not identify bad address or whether client/driver/firmware/configuration is responsible',
            'known_bounds':'negotiated NV12 two planes1280x720, strides1280, capacities921600/460800; H2642MiB; no buffer ERROR observed before poll failure',
            'application_queue_checks':'source fread size/mapped capacities and row lengths checked; exact mem_offset,data_offset and ioctl traces not yet captured',
            'fault_not_pinned_to_specific_frame':'asynchronous pipeline had9 queued/3 returned; decode0..2 does not prove encoded_frame3 caused abort',
            'post_failure_BOOT_SDK_unchanged':True,'post_failure_fpga_state':post['fpga_state'],'device_reset_or_retest':False,'NPU_forward_executed':False,
            'HDMI':{'authorized':True,'target':[1920,1080,60],'BOOT_archive_byte_match':True,'fbdev':False,'DRM_EDID':False,
                    'udmabuf_size':h['udmabuf']['udmabuf0']['size'].strip(),'udmabuf_phys_addr':h['udmabuf']['udmabuf0']['phys_addr'].strip(),
                    'actual_scan_timing':'unknown','reference_mapping_and_safe_stop':'not proven','hardware_written':False,'offline_pattern_prepared':True},
            'scope':'stage stopped on actual hardware firmware error; no full dynamic video, HDMI screen test, RTSP or live combined acceptance'}
    dest.write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result,indent=2))
if __name__=='__main__':main()
