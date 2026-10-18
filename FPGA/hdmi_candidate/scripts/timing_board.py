"""Bounded r12 timing matrix and gated fresh inference/HDMI, on the unchanged r9 BOOT."""
from pathlib import Path,PurePosixPath
import argparse,json,os,shutil,subprocess,tarfile,time,traceback
import segmented_board as common

b=common.b;cfg=common.cfg;ROOT=common.ROOT;PACKAGE=common.PACKAGE;META=common.META
# Reuse FAT safety functions without obsolete manifest/review hash fields.
b.identity_record=lambda value:dict(value,package_id=cfg['package_id'])
CASES=[(20,20),(0,20),(0,0),(20,0)]

def guard():
    auth=b.read_json(common.HERE/'authorization.json')
    b.need(auth['active'] and auth['approved_by']=='user','New timing packet inactive')
    common.require_restore();b.audit(common.ORIGINAL,common.record('restore')['boot_id'])

def verify_shared():
    for name,sha in cfg['shared_files'].items():
        b.need(b.digest(b.regular(PACKAGE/'shared-package'/name))==sha,'Shared protected input changed: '+name)

def execute(name,argv):
    output=ROOT/name;output.mkdir(mode=0o700)
    b.reserve(name,dict(argv=argv,no_retry=True))
    started=time.monotonic()
    with (output/'stdout.log').open('xb') as stdout,(output/'stderr.log').open('xb') as stderr:
        p=subprocess.Popen(argv,cwd=PACKAGE,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,start_new_session=True)
        common.save(name+'-process',dict(pid=p.pid,boot_id=b.boot_id(),started=time.time()))
        while p.poll() is None:
            try:p.wait(timeout=25)
            except subprocess.TimeoutExpired:print(json.dumps(dict(event='still_running',stage=name,pid=p.pid,seconds=time.monotonic()-started,proc=b.proc_snapshot(p.pid))),flush=True)
    result=dict(exit_code=p.returncode,seconds=time.monotonic()-started,pid=p.pid,child_gone=not Path('/proc/'+str(p.pid)).exists(),owners=b.owners(),boot_id=b.boot_id())
    common.save(name+'-process-result',result)
    b.need(result['child_gone'] and not result['owners'],'Child or device owner remains; no further load')
    return output,result

def compare_dma(output,process,sequence,sizes):
    result=dict(passed=False,exit_code=process['exit_code'],sizes=sizes,sequence_before=sequence,files=[],snapshots=[])
    trace=output/'trace.jsonl'
    if trace.exists():
        rows=[json.loads(x) for x in trace.read_text().splitlines()]
        for x in rows:
            if x['event']=='ai_read_monitor_snapshot_raw':result['snapshots'].append(x)
    common.save(output.name+'-raw-review',result)
    if process['exit_code']!=0:return result
    for size in sizes:
        src=Path(str(trace)+'.'+str(size)+'.source.bin');actual=Path(str(trace)+'.'+str(size)+'.actual.bin')
        data=actual.read_bytes();reference=src.read_bytes()
        b.need(len(data)==size and data==reference and data==bytes(((i*37)^(i>>9)^size)&255 for i in range(size)),'Complete DMA bytes differ: '+str(size))
        result['files'].append(dict(bytes=size,source_sha256=b.digest(src),actual_sha256=b.digest(actual),full_equal=True))
    snaps=result['snapshots'];b.need(len(snaps)==len(sizes)+1,'Snapshot count differs')
    for index,s in enumerate(snaps):
        generation=sequence+2*(index+1)
        b.need(s['words_read']==104 and s['generation_before_valid'] and s['generation_after_valid'] and s['status_before']==s['status_after']==0 and s['request_before']==s['response_before']==s['request_after']==s['response_after']==generation,'Snapshot generation/extent failed')
        w=s['words'];b.need(w[0]==0x41495201 and w[3]==0,'ABI or reset error')
        b.need(all(w[8+16*c+3]==0 for c in range(6)),'Accepted nonOKAY response')
        b.need(w[8+16*4]==0 and w[8+16*4+7]==0,'Unexpected idle HDMI activity; stop progression')
    result.update(passed=True,sequence_after=sequence+2*(len(sizes)+1))
    common.save(output.name+'-review',result)
    return result

def main(stage):
    if stage=='prepare':
        result=common.main('prepare')
        target=PACKAGE/'shared-package';target.mkdir(mode=0o700)
        expected=cfg['shared_files'];seen=set();total=0
        with tarfile.open(PACKAGE/'shared-package.tar') as archive:
            members=archive.getmembers();b.need(len(members)==len(expected)==15,'Shared archive member count changed')
            for m in members:
                p=PurePosixPath(m.name);total+=m.size
                b.need(m.isfile() and not p.is_absolute() and '..' not in p.parts and m.name in expected and m.name not in seen and total<=50*1024*1024,'Unsafe shared member')
                seen.add(m.name);out=target.joinpath(*p.parts);out.parent.mkdir(exist_ok=True,parents=True)
                with archive.extractfile(m) as source,out.open('xb') as dest:shutil.copyfileobj(source,dest)
        verify_shared();os.chmod(target/'pose_hdmi_demo',0o700)
        os.chmod(PACKAGE/'ai_read_segmented_probe',0o700)
        return result
    if stage=='timing':
        guard();b.verify_file(PACKAGE/'ai_read_segmented_probe',cfg['files']['ai_read_segmented_probe']);b.reserve('timing')
        studies=[]
        for index,(open_ms,after64_ms) in enumerate(CASES):
            seq=index*6;name='case-'+str(index)
            output,process=execute(name,[str(PACKAGE/'ai_read_segmented_probe'),str(ROOT/name/'trace.jsonl'),str(open_ms),str(after64_ms),str(seq),'4096'])
            review=compare_dma(output,process,seq,[64,4096]);studies.append(dict(case=index,waits=[open_ms,after64_ms],**review))
            if not review['passed']:return common.save('timing',dict(passed=False,stopped_at_case=index,cases=studies,no_later_loads=True))
        return common.save('timing',dict(passed=True,cases=studies,next_sequence=24))
    if stage=='full-dma':
        guard();b.need(common.record('timing')['passed'],'Timing stage did not pass')
        name='full-dma';output,process=execute(name,[str(PACKAGE/'ai_read_segmented_probe'),str(ROOT/name/'trace.jsonl'),'20','20','24','1048576'])
        review=compare_dma(output,process,24,[64,4096,65536,1048576]);return common.save('full-dma',review)
    if stage=='shared':
        guard();b.need(common.record('full-dma')['passed'] and common.record('full-dma')['sequence_after']==34,'Complete DMA gate absent')
        verify_shared();name='shared';target=PACKAGE/'shared-package'
        output,process=execute(name,[str(target/'pose_hdmi_demo'),str(target),str(ROOT/name/'inference'),'--allow-device-init'])
        return common.save('shared',dict(process,hardware_and_numeric_review_required=True,visual_confirmation_required=True))
    return common.main(stage)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['prepare','install','candidate-reboot','restore','timing','full-dma','shared','fallback-reboot','audit','close']);args=parser.parse_args()
    try:print(json.dumps(main(args.stage),ensure_ascii=False,indent=2),flush=True)
    except BaseException:traceback.print_exc();raise SystemExit(1)
