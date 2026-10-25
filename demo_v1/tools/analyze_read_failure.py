"""只比较已保存原值；不连接设备，不把晚读写回任何推理输入。"""
from pathlib import Path
import argparse, collections, json, math, struct

def main():
    p=argparse.ArgumentParser(); p.add_argument('results',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    root=a.results; failure=root/'failed-host-inputs'
    report={}
    metadata=root/'copy-observations/metadata.jsonl'
    if metadata.exists():
        rows=[json.loads(s) for s in metadata.read_text().splitlines()]
        names=['before_wait_layer_count','after_wait_layer_count','before_copy_layer_count','after_copy_layer_count']
        report['rolling_metadata_rows']=len(rows)
        report['layer_count_observations']={n:dict(collections.Counter(str(r[n]) for r in rows if n in r)) for n in names}
        report['last_rows']=rows[-4:]
        report['counts_prove_DMA_cache_fence']=False
    if (failure/'failure.json').exists():
        original=(failure/'input1.f32').read_bytes(); data=(failure/'input0.f32').read_bytes()
        shadow=(failure/'post-copy/input1.f32').read_bytes()
        later=[(failure/('source-readback/round%d.input1.f32'%n)).read_bytes() for n in range(2)]
        words=lambda b:[b[i:i+4] for i in range(0,len(b),4)]
        first=words(original); source=words(data); late=words(later[0])
        values=struct.unpack('<%df'%len(first),original)
        invalid=[i for i,v in enumerate(values) if not math.isfinite(v) or v!=math.trunc(v) or not 0<=v<180]
        changed=[i for i in range(len(first)) if first[i]!=late[i]]
        blocks=[]
        for i in changed:
            if blocks and blocks[-1]['end']+1==i:blocks[-1]['end']=i;blocks[-1]['count']+=1
            else:blocks.append({'begin':i,'end':i,'count':1})
        report['failure']=json.loads((failure/'failure.json').read_text())
        report['first_Host_equals_independent_shadow']=original==shadow
        report['two_late_reads_equal']=later[0]==later[1]
        report['illegal_first_indices']=len(invalid)
        report['changed_indices']=len(changed)
        report['changed_words_equal_preceding_input_same_offset']=sum(first[i]==source[i] for i in changed if i<len(source))
        report['changed_blocks']=blocks
        report['first_illegal']=[{'index':i,'value':values[i],'raw_LE_hex':first[i].hex()} for i in invalid[:8]]
        report['late_reads_used_for_repair']=False
        report['input0_unchanged_across_shadow_and_reads']=all(data==(failure/n).read_bytes() for n in ['post-copy/input0.f32','source-readback/round0.input0.f32','source-readback/round1.input0.f32'])
    else: report['first_read_failure_captured']=False
    a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['last_rows','changed_blocks','failure']},indent=2))

if __name__=='__main__':main()
