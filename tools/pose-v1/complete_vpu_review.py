"""Join immutable hardware, transfer, bitstream and host decode evidence."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'tools/pose-v1/evidence/vpu-20261007-r1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    out=P/'completion-review.json';assert not out.exists()
    data=P/'encode-r4/results'
    for line in (data/'video-transfer.sha256').read_text().splitlines():
        h,name=line.split('  ',1);assert name in ('video.h264','review.mp4') and sha(data/name)==h
    for name in ('probe-h264','probe-mp4','remux'):
        assert int((data/f'{name}.exit.txt').read_text())==0
    mp4=read(P/'host-review/review.json');raw=read(P/'host-review-raw-r2/review.json')
    assert [r['decoded_bgr_sha256'] for r in mp4['records']]==[r['decoded_bgr_sha256'] for r in raw['records']]
    assert mp4['all_frame_ids_correct'] and mp4['decoded_frames']==30
    # Bounded generic Annex-B start-code parser, no fixed SPS/PPS offsets.
    bitstream=(data/'video.h264').read_bytes();starts=list(re.finditer(b'\x00\x00\x00?\x01',bitstream));assert starts and starts[0].start()==0
    nals=[]
    for i,m in enumerate(starts):
        end=starts[i+1].start() if i+1<len(starts) else len(bitstream)
        assert m.end()<end
        header=bitstream[m.end()];assert not header&0x80
        nals.append({'offset':m.start(),'prefix_bytes':m.end()-m.start(),'payload_bytes':end-m.end(),'type':header&31})
    counts=dict(Counter(n['type'] for n in nals));assert counts.get(7) and counts.get(8) and counts.get(5)
    probe=read(data/'probe-mp4.json');assert probe['format']['duration']=='3.000000'
    s=probe['streams'][0];assert s['codec_name']=='h264' and s['profile']=='Constrained Baseline' and s['nb_read_frames']=='30'
    build=read(P/'build-r4-review.json');hw=read(P/'encode.review.json');neg=read(P/'negotiate.review.json')
    assert build['program_sha256']==hw['program_sha256']==neg['program_sha256']
    report={'status':'independent_VPU_H264_file_and_host_decode_passed','program_sha256':build['program_sha256'],
            'input_sha256':hw['input_sha256'],'h264_sha256':sha(data/'video.h264'),'mp4_sha256':sha(data/'review.mp4'),
            'encoded_bytes':len(bitstream),'mp4_bytes':(data/'review.mp4').stat().st_size,'frames':30,'width':1280,'height':720,'fps':10,'duration_seconds':3,
            'requested_bitrate':2000000,'actual_profile':s['profile'],'NAL_type_counts':counts,'NAL_records':nals,
            'source_ids_all_correct':True,'raw_and_mp4_decoded_pixels_identical':True,'kernel_unchanged':True,'exit':0,'encoder_stderr_empty':True,
            'host_decoder':'existing PI_wifi_sensing OpenCV5.0.0 FFmpeg avcodec61.19.100','no_dependencies_installed':True,
            'RGB_mean_abs_8bit':mp4['RGB_mean_abs_8bit'],'RGB_max_abs_8bit':mp4['RGB_max_abs_8bit'],'RGB_PSNR_dB':mp4['RGB_PSNR_dB'],
            'HDMI_target':[1920,1080,60],'HDMI_paused':True,'HDMI_timing_hardware_modified':False,
            'NPU_executed':False,'RTSP_executed':False,'live_dual_route_verified':False,'system_performance_verified':False,
            'limitations':['synthetic prerecorded renderer plus moving ID/marker, no live inference during encoding',
                           'offline MP4 nominal10fps reconstructed; not preserved container capture timestamps',
                           'ffprobe lacks explicit color metadata; negotiated601-limited does not prove H264 VUI color signaling',
                           'lossy RGB statistics include host conversion conventions; no color calibration or numerical acceptance',
                           '3-second finite test does not establish sustained throughput or long-run stability'],
            'historical_failures':['r1 CRLF checksum stopped before preflight/program','r2 coded2x2 stopped before buffers/stream',
                                   'r3 negotiated coded default709-full, superseded before streaming',
                                   'first raw host review applied MP4 rate assertion to nakedH264, raw metadata25fps/negativecount untrusted; preserved and separate AnnexB mode used'],
            'remux_warning':(data/'remux.stderr.log').read_text().strip()}
    out.write_bytes((json.dumps(report,indent=2)+'\n').encode())
    checkpoint={'status':'V2_file_encode_host_review_complete_HDMI_paused','read_first':['tools/pose-v1/VPU-RESULTS-20261007.md','tools/pose-v1/evidence/vpu-20261007-r1/completion-review.json'],
                'next':'bounded encoder interface / timestamp and color metadata / prerecorded real renderer frames / independent RTSP under approved full-flow scope',
                'HDMI':'user paused; target1080p60, clock/scanout mapping still to establish when resumed',
                'sessions_closed':True,'do_not_repeat_passed_stage':True}
    (P/'next-checkpoint.json').write_bytes((json.dumps(checkpoint,indent=2)+'\n').encode())
    print(json.dumps({k:v for k,v in report.items() if k not in ('NAL_records','historical_failures','limitations')},indent=2))

if __name__=='__main__':main()
