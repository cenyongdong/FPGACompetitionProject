"""Keep strict full107 gate; review only actually captured failure prefix."""
from pathlib import Path
root=Path(__file__).resolve().parents[2];s=(root/'tools/pose-v1/review_picture_video.py').read_text(encoding='utf-8')
s=s.replace("assert summary['joined'] and summary['drained'] and summary['published']==summary['consumed']==107 and not summary['overwritten'] and not summary['coalesced']","assert summary['joined'] and not summary['drained'] and summary['published']==summary['consumed']==20 and not summary['overwritten'] and not summary['coalesced']")
s=s.replace('assert len(pictures)==len(calls)==107 and 2<=len(samples)==summary[\'submitted\']==summary[\'returned\']<1000','assert len(pictures)==len(calls)==20 and 2<=len(samples)<1000')
s=s.replace('range(-1,107)','range(-1,20)').replace('len(images)==len(samples) and len(headers)==len(last)==1','0<len(images)<=len(samples) and len(headers)==1 and not last')
s=s.replace("assert [x['pts_us'] for x in queued]==[x['pts_us'] for x in images]==[x['pts_us'] for x in clock]", "assert [x['pts_us'] for x in queued[:len(images)]]==[x['pts_us'] for x in images] and [x['pts_us'] for x in queued]==[x['pts_us'] for x in clock]")
s=s.replace('0<=key<107','0<=key<20').replace('len(records)==len(samples) and seen-{ -1 }==set(range(107))','len(records)==len(images) and seen-{ -1 }<=set(range(20))')
s=s.replace('==list(range(107))','==list(range(20))')
s=s.replace("status='real_owned_picture_NV12_sources_and_actual_PTS_video_passed'","status='failed_picture_captured_prefix_NV12_and_sources_checked_not_acceptance'")
s=s.replace('unique_real_sources=107,NV12_files=108','unique_real_sources=len(seen-{-1}),completed_real_sources=20,uncaptured_sample_tail=len(samples)-len(images),submitted_as_logged=len(queued),NV12_files=21')
s=s.replace('NV12_bytes_compared=108*1382400','NV12_bytes_compared=21*1382400')
s=s.replace("sum(not x['inference_result'] for x in samples)","sum(not x['inference_result'] for x in samples[:len(images)])").replace("sum(x['repeated_source'] for x in samples)","sum(x['repeated_source'] for x in samples[:len(images)])")
p=root/'tools/pose-v1/review_picture_video_prefix.py';assert not p.exists();p.write_text(s,encoding='utf-8',newline='\n')
