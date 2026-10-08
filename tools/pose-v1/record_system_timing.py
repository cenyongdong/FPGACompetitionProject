"""Freeze finite measurement results, actual-consumer coverage and final resource evidence."""
import hashlib,json,re
from pathlib import Path
import mixed_validation_gate as old

root=old.ROOT;directory=root/'tools/pose-v1/evidence/system-timing-20261008-r2'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
host=load(directory/'host-check.acceptance.json');assert host['Host_cases']==107 and host['CPU_FP32']==59600
stages=[load(directory/(name+'.acceptance.json')) for name in ('measure-2hz','measure-5hz')]
video=[load(directory/(name+'/review.json')) for name in ('measure-2hz-video-v2','measure-5hz-video-review')]
network=[load(directory/(name+'-network-review/review.json')) for name in ('measure-2hz','measure-5hz')]
assert all(s['full_numeric_bitwise'] and s['binary_sha256']==host['binary_sha256'] and s['steady_clock_only'] for s in stages)
assert all(n['all_sources_present'] and n['all_pixels_equal_current_capture'] and n['actual_RTP_capture_PTS'] for n in network)
final=directory/'final-state';assert old.verify(final)==8
assert not any(':'+str(p)+' ' in (final/'ports.txt').read_text() for p in (39001,8554))
assert not any(line.split(None,1)[-1].startswith('/tmp/pose-system-timing-20261008-r2/pose_live_pipeline_check') for line in (final/'processes.txt').read_text().splitlines())
assert (final/'dmesg.log').read_bytes()==(directory/'measure-5hz/dmesg.after.log').read_bytes()
mem={line.split(':')[0]:int(line.split()[1]) for line in (final/'meminfo.txt').read_text().splitlines() if line.startswith(('MemAvailable:','CmaTotal:','CmaFree:'))}
high=sum(sum(int(x) for x in line.split()[11:]) for line in (final/'buddyinfo.txt').read_text().splitlines())
# NAL types prove that the capture metric points to a VCL packet, not only SPS/PPS.
for name in ('measure-2hz','measure-5hz'):
    out=directory/name/'results';packets=[json.loads(x) for x in (out/'packets.jsonl').read_text().splitlines()];blob=(out/'encoder/video.h264').read_bytes();position=0;vcl={}
    for packet in packets:
        data=blob[position:position+packet['bytes']];position+=packet['bytes'];starts=list(re.finditer(b'\x00\x00(?:\x00)?\x01',data))
        if any(data[s.end()]&31 in (1,5) for s in starts):vcl[packet['pts_us']]=packet['capture_ns']
    assert position==len(blob)
    samples=[json.loads(x) for x in (out/'samples.jsonl').read_text().splitlines()]
    for au in [json.loads(x) for x in (out/'access-units.jsonl').read_text().splitlines()]:
        # Bootstrap SPS/PPS share NoInput id0 PTS; only measured real-source VCL is relevant.
        if not samples[au['encoded_id']]['inference_result']:continue
        selected=next(p for p in packets if p['pts_us']==au['pts_us'] and p['bytes']>0)
        assert selected['capture_ns']==vcl[au['pts_us']]
report=dict(status='bounded_whole_system_measurement_complete_5Hz_not_met',program_sha256=host['binary_sha256'],manifest_sha256=host['package_manifest_sha256'],payloads=403,build_sources=48,Host_cases=107,CPU_FP32=59600,total_forwards=sum(s['consumed'] for s in stages),full_output_FP32=sum(s['consumed']*15100 for s in stages),all_actual_consumers_bitwise_reference=True,encoded_frames=sum(s['encoded'] for s in stages),network_frames=sum(n['network_frames'] for n in network),joint_checks=sum(v['joint_visibility_checks'] for v in video),actual_sources_PTS_pixels=True,load5_sent=33,load5_consumed=stages[1]['consumed'],load5_overwritten=stages[1]['overwritten'],load5_measurements=stages[1]['measured_consumed'],effective5load_Hz=stages[1]['new_pose_completion_interval_Hz'],picture_P95_ms=stages[1]['metrics']['arrival_to_picture_ms']['P95'],RTSP_handoff_P95_ms=stages[1]['metrics']['arrival_to_RTSP_handoff_ms']['P95'],serial_display_mean_ms=stages[1]['metrics']['draw_ms']['mean']+stages[1]['metrics']['NV12_ms']['mean'],whole_5Hz_verified=False,long_run_verified=False,HDMI_verified=False,SDK_model_BOOT_frame_protocol_unchanged=True,new_compactions_cache_clear_reboots=0,independent_VPU_starts_this_batch=2,final_memory=mem,final_order7_and_higher_free_blocks=high,final_high_order_snapshot_not_startup_guarantee=True,persistent_memory_leak_proven=False,services_running=False,SSH_SFTP_closed=True,warm_NoInput_reference_external_explicit=True,review_sha256={str(p.relative_to(directory)):sha(p) for p in [directory/'build.acceptance.json',directory/'host-check.acceptance.json',directory/'measure-2hz.acceptance.json',directory/'measure-5hz.acceptance.json']+[directory/(name+'/review.json') for name in ('measure-2hz-video-v2','measure-5hz-video-review','measure-2hz-network-review','measure-5hz-network-review')]},supplementary_video_reviewer_sha256=sha(root/'tools/pose-v1/review_system_video.py'))
assert report['final_order7_and_higher_free_blocks']==0
p=directory/'completion-review.json';assert not p.exists();p.write_text(json.dumps(report,indent=2)+'\n')
checkpoint=dict(status='system_timing_complete_prepare_owned_output_worker_and_startup_conditions',active_tests=False,services_running=False,SSH_SFTP_closed=True,build='.local/pose-v1-build/mixed-20261008-system-timing-r2',package='.local/pose-v1-system-timing/package-20261008-r2',board='/tmp/pose-system-timing-20261008-r2',program_sha256=host['binary_sha256'],completion_sha256=sha(p),whole5Hz=False,compaction_not_authorized_again=True,final_high_order_free_blocks=0,next='Read SYSTEM-TIMING-RESULTS-20261008.md and SYSTEM-TIMING-NEXT-20261008.md. Isolate owned output rendering/conversion while preserving main-owned Engine; do not move SDK to a worker. Restore/establish first-start resource conditions only by reviewed matched allocation design or explicit recovery choice; no automatic compaction/reboot/cache clearing. Prepare new sources/Host checks, then finite numeric/source/performance regression; current timings are baseline, not 5Hz acceptance.')
(directory/'next-checkpoint.json').write_text(json.dumps(checkpoint,indent=2)+'\n');print(json.dumps(report,indent=2))
