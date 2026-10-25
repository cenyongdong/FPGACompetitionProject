"""Reinterpret the saved, complete second FREEZE; no MMIO or command replay."""
import hashlib
import json
import capture_deferred as c


def revalidate(run, boot_id):
    read=lambda p:json.loads(p.read_text())
    failed=read(run/'consume/capture/result.json')
    c.need(failed.get('valid') is False and failed.get('boot_id')==boot_id and
           failed.get('error')=='Full raw retained; monitor/boot/release snapshot identity invalid',
           'Only the saved second-FREEZE parser failure may be revalidated')
    before=read(run/'observe-before/capture/result.json')['normalized']
    seed=read(run/'metadata/before-seed.json')
    c.need(before['valid'] and before['boot_id']==boot_id and seed['eligible'] and
           seed['classification']=='known_unmatched_return' and seed['boot_id']==boot_id,
           'Original same-boot known seed missing')
    path=run/'consume/capture/raw.jsonl'
    payload=path.read_bytes()
    rows=[json.loads(x) for x in payload.splitlines()]
    def one(event):
        values=[r for r in rows if r['event']==event]
        c.need(len(values)==1,'Unique raw event required: '+event)
        return values[0]
    begin=one('begin')
    c.need(begin['operation']=='consume' and begin['actual_boot_id']==begin['expected_boot_id']==boot_id,
           'Original raw boot identity differs')
    c.need(one('owners')['owners']==[], 'Original command had another owner')
    c.need(one('inconclusive')['error']==failed['error'], 'Original failure context differs')
    initial=one('monitor_initial')['header']
    wr,br,rr=one('monitor_words_raw'),one('boot_words_raw'),one('release_words_raw')
    h,end=wr['header'],rr['header_after']
    words,boot,release=wr['words'],br['words'],rr['words']
    c.need(len(words)==104 and len(boot)==19 and len(release)==128,'Full native raw bundles missing')
    c.need(initial['request']==initial['response']==before['observer_generation']==2 and
           initial['status']==0 and initial['abi']==0x41495201 and
           h==end and h['status']==0 and h['abi']==0x41495201 and h['request']==h['response']==4,
           'Actual first-to-second complete monitor epochs differ')
    c.need(words[0]==0x41495201 and boot[0]==0x42545201 and boot[18]&128 and
           release[0]==0x50534c01 and release[1]&3==3 and release[7]==h['request']//2==2,
           'Actual source FREEZE counter is not the second completed snapshot')
    c.need(boot[3]==release[36] and boot[4]==release[37], 'Matched PS source totals differ')
    expected=[(c.MON,1),(c.CTRL,c.CONS),(c.CTRL,c.SNAP),(c.MON,2)]
    attempts=[r for r in rows if r['event']=='command_attempt']
    acks=[r for r in rows if r['event']=='command_ack']
    c.need([(int(r['offset'],16),r['value']) for r in attempts]==expected and
           all(r['boot_id']==boot_id for r in attempts) and
           [(int(r['base'],16),r['command']) for r in acks]==expected,
           'Original command attempts/ACKs were not exactly one ARM/CONS/SNAP/FREEZE')
    c.need([r['header']['request'] for r in acks]==[3,2,3,4] and
           all(r['header']['request']==r['header']['response'] and r['header']['status']&3==0 for r in acks),
           'Original ACK generations/status differ')
    controls=[r['raw'] for r in rows if r['event']=='control_raw']
    c.need(len(controls)==2 and controls[0]==before['control']['raw'],
           'Original held-before control snapshot differs')
    held=controls[1]
    class SavedControl:
        def read(self,offset):
            off=offset-c.CTRL
            if off in (0,4,8,12):
                return held['header_before'][{0:'status',4:'abi',8:'request',12:'response'}[off]]
            return held['words_10_to_38'][(off-0x10)//4]
    class NoDeviceLog:
        def save(self,*a,**kw):pass
    c.need(held['header_before']==held['header_after'],'Saved control header changed during read')
    control=c.read_control(SavedControl(),NoDeviceLog())
    raw=dict(initial_generation=2,generation=4,words=words,boot_words=boot,
             release_words=release,header_after=end)
    after=c.normalize(raw,control,boot_id,before)
    after['control'].update(arm_request=acks[1]['header']['request'],
        snapshot_request=acks[2]['header']['request'],
        commands=[dict(opcode=r['command'],request=r['header']['request']) for r in acks[1:3]])
    c.need(c.safe_terminal(after['drain']),'Saved consume did not reach safe terminal')
    return dict(valid=True,operation='revalidate-consume',boot_id=boot_id,raw_snapshot=raw,
        normalized=after,original_raw_sha256=hashlib.sha256(payload).hexdigest(),
        original_failure_preserved=True,original_exit_code=2,MMIO_commands=0,
        automatic_retry=False,SDK=0,DMA=0,HDMI_START=0,functional_recovery_proved=False)
