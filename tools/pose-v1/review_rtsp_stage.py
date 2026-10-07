"""Independent finite RTSP transport/decode/identity and resource review."""
import argparse
import hashlib
import json
from pathlib import Path
from review_vpu_sequence_stage import check_manifest

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);p.add_argument('--package',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    e=a.evidence;b=e/'board';m=json.loads((a.package/'manifest.json').read_text())
    payloads=check_manifest(a.package,a.package/'files.sha256')
    returned=check_manifest(b,b/'files.sha256','run-replay')
    assert m['program_sha256']==sha(a.package/'pose_rtsp_replay_check')
    assert m['h264_sha256']==sha(a.package/'video.h264')
    assert (b/'exit.txt').read_text().strip()=='0'
    assert (b/'dmesg.before.log').read_bytes()==(b/'dmesg.after.log').read_bytes()
    identity=json.loads((b/'preflight.json').read_text())
    assert identity['fpga_state']=='operating'
    assert identity['SDK_packages']==['customop arm64 3.39.0','icraft arm64 3.39.0']
    baseline=json.loads((Path(__file__).parent/'evidence/video-descriptor-20261007-r5/encode/preflight.json').read_text())
    assert identity['boot_files']==baseline['boot_files'] and identity['libraries']==baseline['libraries']
    assert ':8554' not in (b/'listeners.before.txt').read_text() and ':8554' not in (b/'listeners.after.txt').read_text()
    events=[json.loads(line) for line in (b/'results/events.jsonl').read_text().splitlines()]
    assert events[0]=={'event':'ready','port':8554,'frames':54,'seconds':60,'vpu':False,'npu':False,'hdmi':False}
    final=events[-1]
    assert final['event']=='completed' and not final['failed'] and final['sources_live']==0
    assert 60000000<=final['elapsed_us']<65000000
    assert not any(event['event']=='failure' for event in events)
    created={x['source']:x for x in events if x['event']=='source_created'}
    assert len(created)==final['sources_created']==3
    assert set(created)=={x['source'] for x in events if x['event']=='source_closed'}
    assert any(x['start_encoded_frame']!=0 for x in created.values()),'No mid-sequence IDR join exercised'
    # Preserve and classify exact diagnostics emitted by the supplied library.
    stderr=(b/'stderr.log').read_text().splitlines()
    assert stderr==['CJN-Trace>>RTCPInstance::RTCPInstance: maxRTCPPacketSize=4000000']*2
    clients=[]
    decoded=json.loads((e/'host-decode/review.json').read_text());assert decoded['status']=='RTSP_host_200_frames_decoded_verified'
    for i in (1,2):
        directory=e/f'clients/client{i}';client=json.loads((directory/'review.json').read_text())
        assert client['status']=='finite_RTSP_RTP_verified' and len(client['frames'])==100
        assert len(client['keepalives'])>=3 and all(k['response']==200 for k in client['keepalives'])
        assert client['sequence_gaps']==0 and client['SDP_actual_parameter_sets'] and client['RTP_step_ticks']==9000
        assert sha(directory/'received.h264')==client['reconstructed_h264_sha256']
        assert client['frames'][0]['idr']
        for prior,current in zip(client['frames'],client['frames'][1:]):
            assert current['encoded_id']==(prior['encoded_id']+1)%54
            assert (current['timestamp']-prior['timestamp'])&0xffffffff==9000
        host=decoded['clients'][i-1]
        assert host['frames']==100 and host['all_frame_ids_correct'] and host['all_decoded_pixels_equal_r5']
        # Associate network frames with the corresponding actual server source.
        actual=[x for x in events if x['event']=='nal_delivered' and x['source']==i and x['type'] in (1,5)]
        assert len(actual)>=100 and [x['encoded_frame'] for x in actual[:100]]==[x['encoded_id'] for x in client['frames']]
        clients.append({'client':i,'received_frames':100,'first_encoded_id':client['frames'][0]['encoded_id'],
                        'last_encoded_id':client['frames'][-1]['encoded_id'],'keepalive_count':len(client['keepalives']),
                        'RTP_packets':sum(x['event']=='rtp' for x in client['packets']),
                        'RTCP_packets':sum(x['event']=='rtcp' for x in client['packets']),
                        'decoded_exact_r5':True,'NAL_exact_r5':True,'received_h264_sha256':client['reconstructed_h264_sha256']})
    result={'status':'isolated_RTSP_transport_reconnect_decode_verified','scope':'owned prerecorded VPU output; no concurrent VPU or inference',
            'program_sha256':m['program_sha256'],'source_sha256':m['source_sha256'],'package_sha256':sha(a.package/'files.sha256'),
            'package_payloads':payloads,'returned_hashed_files':returned,'exit':0,'kernel_unchanged':True,'boot_sdk_unchanged':True,
            'stderr_empty':False,'stderr_classification':'two exact vendor RTCP diagnostic lines, retained',
            'completion':final,'clients':clients,'port_released':True,'all_sources_released':True,
            'color_VUI_verified':False,'whole_system_5Hz_verified':False,'HDMI_mode_changed':False}
    a.output.write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps(result,indent=2))

if __name__=='__main__':main()
