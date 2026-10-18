"""Independent, queue-based review of actual AXI stream simulation handshakes."""
from pathlib import Path
from collections import defaultdict,deque,Counter
import csv,json,hashlib,re,shutil
R=Path(__file__).resolve().parents[3]
S=R/'tools/pose-v1/evidence/hdmi-live-20261017-r3/generated-axi-stream-r1'
E=S.parent/'generated-axi-stream-independent-r2'

def main():
    E.mkdir(exist_ok=False)
    shutil.copyfile(Path(__file__),E/'actual-source.py')
    assert json.loads((S/'result.json').read_text())['passed']
    steps=json.loads((S/'execution.json').read_text());assert len(steps)==4 and all(x['exit']==0 and not x['timeout'] for x in steps)
    source_queues=defaultdict(deque);master_queues=defaultdict(deque);source={};master={};seen_master_beats={};counts=Counter()
    source_live=[0,0];source_peak=[0,0];master_live=0;master_peak=0;accepted_order=[];reordered=0;terminal_metadata=[]
    sizes=set();ids=[set(),set()];resps=set();page_end=0;previous_cycle=-1
    path=S/'generated_axi3_stream.csv'
    def length(seq):return (1,2,8,16)[seq%4]
    def response(seq):return 2 if seq%13==0 else 3 if seq%17==0 else 0
    def addr(src,seq):return 0x01000000+src*0x08000000+seq*4096+(4096-8*length(seq) if seq%8>=4 else 64*(seq%4))
    def thread(seq):return seq%32 if seq<192 else seq%4
    def expected(src,seq,beat):return 0xc35a691700000000 ^ (0x1000000000000000*src) ^ (0x10001*seq) ^ (0x0101010101010101*beat)
    with path.open(newline='') as stream:
        reader=csv.DictReader(stream)
        for row in reader:
            event=row['event']
            if event in ('SUMMARY','STALLS'):
                terminal_metadata.append(row);continue
            assert not terminal_metadata,'Handshake appeared after terminal records'
            assert event in ('S_AR','M_AR','M_R','S_R'),row
            cycle=int(row['cycle']);src=int(row['source']);seq=int(row['sequence']);identity=int(row['id'])
            address=int(row['address_hex'],16);beat=int(row['beat']);beats=int(row['burst_beats']);last=int(row['last']);resp=int(row['resp']);data=int(row['data_hex'],16)
            assert cycle>=previous_cycle and src in (0,1) and 0<=seq<256,(event,row)
            previous_cycle=cycle;key=(src,seq);assert address==addr(src,seq) and beats==length(seq),row
            if event=='S_AR':
                assert key not in source and identity==thread(seq)
                source[key]={'beats':0,'complete':False};source_queues[src,identity].append(key)
                source_live[src]+=1;source_peak[src]=max(source_peak[src],source_live[src]);ids[src].add(identity);sizes.add(beats)
                assert address%8==0 and address%4096+8*beats<=4096
                page_end+=int(address%4096+8*beats==4096)
            elif event=='M_AR':
                assert key in source and key not in master and identity==32*src+thread(seq)
                master[key]={'beats':0,'complete':False};master_queues[identity].append(key);accepted_order.append(key)
                master_live+=1;master_peak=max(master_peak,master_live)
            else:
                assert last==int(beat==beats-1) and resp==response(seq),row
                resps.add(resp)
                if event=='M_R':
                    assert identity==32*src+thread(seq) and master_queues[identity] and master_queues[identity][0]==key
                    assert master[key]['beats']==beat
                    if beat==0 and accepted_order[0]!=key:reordered+=1
                    master[key]['beats']+=1;seen_master_beats[src,seq,beat]=(resp,last,data)
                    if resp==0:assert data==expected(src,seq,beat)
                    if last:
                        master[key]['complete']=True;master_queues[identity].popleft();accepted_order.remove(key);master_live-=1
                else:
                    assert identity==thread(seq) and source_queues[src,identity] and source_queues[src,identity][0]==key
                    assert source[key]['beats']==beat and (src,seq,beat) in seen_master_beats
                    mr=seen_master_beats[src,seq,beat];assert (resp,last)==mr[:2]
                    if resp==0:assert data==mr[2]==expected(src,seq,beat)
                    source[key]['beats']+=1
                    if last:source[key]['complete']=True;source_queues[src,identity].popleft();source_live[src]-=1
            counts[event]+=1
    assert counts==Counter({'S_AR':512,'M_AR':512,'M_R':3456,'S_R':3456}),counts
    assert all(x['complete'] and x['beats']==length(k[1]) for k,x in source.items())
    assert all(x['complete'] and x['beats']==length(k[1]) for k,x in master.items())
    assert source_live==[0,0] and master_live==0 and not accepted_order
    assert all(not q for q in source_queues.values()) and all(not q for q in master_queues.values())
    assert master_peak==8 and max(source_peak)<=8 and reordered>0 and page_end==256
    assert ids==[set(range(32)),set(range(32))] and sizes=={1,2,8,16} and resps=={0,2,3}
    assert [r['event'] for r in terminal_metadata]==['SUMMARY','STALLS']
    result={'passed':True,'handshakes':dict(counts),'peak_downstream_outstanding':master_peak,
        'source_event_prefix_peaks':source_peak,'different_ID_reordered_bursts':reordered,'bursts_ending_at_4KiB':page_end,
        'lengths':sorted(sizes),'IDs_per_source':[len(i) for i in ids],'responses':sorted(resps),
        'error_response_data':'not compared: AXI does not define error response payload correctness',
        'scope':'Independent trace conservation/routing/per-ID FIFO review; no PS/AI_Mate/DDR hardware or physical timing validation',
        'CSV_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'terminal_metadata':terminal_metadata}
    shutil.copyfile(Path(__file__),E/'actual-source.py')
    (E/'review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
