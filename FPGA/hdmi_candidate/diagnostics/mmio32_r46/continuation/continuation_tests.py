"""Regression and unsafe-state rejection using saved r46 data; no board access."""
from pathlib import Path
import copy, json, sys, importlib.util, hashlib, uuid, contextlib
W=Path(__file__).resolve().parent;D=W/'continuation';P=D/'package'
E=Path('D:/FPGACompetitionProject/tools/pose-v1/evidence/hp2-mmio32-20261024-r46')
sys.dont_write_bytecode=True;sys.path.insert(0,str(P))
import revalidate_consume as r, consume_gate as g, capture_deferred as c
run=E/'board-candidate/run-1'
read=lambda p:json.loads(p.read_text())
before=read(run/'observe-before/capture/result.json')['normalized']
actual=r.revalidate(run,before['boot_id'])
after=actual['normalized']
trace=copy.deepcopy(read(run/'post-stop-readonly/cycletrace.decoded.json')['banks'][1])
trace.update(valid=True,boot_id=before['boot_id'],overflow=False,arm_HP_cycle=after['control']['arm_HP_cycle_raw']+1)
pb=read(run/'protocol-before/raw.decoded.json');pa=read(run/'post-stop-readonly/protocol.decoded.json')
for p,v in ((pb,before),(pa,after)):
    p.update(valid=True,capture_HP_cycle=v['control']['capture_HP_cycle'],live_status=v['control']['full_PC_status'])
fixture=[before,after,trace,pb,pa];cases=[]
def check(name,fn):
    try:fn();cases.append(dict(name=name,passed=True))
    except Exception as e:cases.append(dict(name=name,passed=False,error=str(e)))
def need(ok):assert ok
def rejects(edit):
    f=copy.deepcopy(fixture);edit(f);need(g.evaluate(*f)['eligible'] is False)
gate=g.evaluate(*fixture)
check('actual_second_FREEZE2_normalizes_no_MMIO',lambda:need(actual['MMIO_commands']==0 and after['observer_generation']==4 and actual['original_exit_code']==2))
check('actual_16_beats_safe_before_checker_rearm',lambda:need(gate['eligible'] and gate['discard_beats']==16 and gate['buffered_before']==6 and gate['buffered_after']==0 and gate['consumption_CAM_underflow_retained']))
check('raw_79_retained_requires_fresh_checker',lambda:need(after['control']['full_PC_status']>>79&1 and gate['checker_only_rearm_required'] and gate['fresh_functional_160_bit_gate_unchanged']))
check('79_before_consumption_forbidden',lambda:rejects(lambda f:f[3].update(live_status=f[3]['live_status']|1<<79)))
check('78_capacity_overflow_after_forbidden',lambda:rejects(lambda f:f[4].update(live_status=f[4]['live_status']|1<<78)))
check('unknown80_after_forbidden',lambda:rejects(lambda f:f[4].update(live_status=f[4]['live_status']|1<<80)))
check('79_in_frozen_startup_window_forbidden',lambda:rejects(lambda f:f[4]['rows'][0].update(PC_status=f[4]['rows'][0]['PC_status']|1<<79)))
check('AR_after_forbidden',lambda:rejects(lambda f:f[1]['counts_lifetime']['PS'].update(AR=1)))
check('bad_response_forbidden',lambda:rejects(lambda f:f[1]['drain'].update(saw_RRESP_error=True)))
check('buffered_beat_loss_forbidden',lambda:rejects(lambda f:f[1]['counts_lifetime']['S01'].update(R=15)))
check('second_ARM_bookkeeping_forbidden',lambda:rejects(lambda f:f[1]['control']['commands'].append(dict(opcode=c.CONS,request=4))))
check('trace_gap_forbidden',lambda:rejects(lambda f:f[2]['rows'][10].update(HP_cycle=f[2]['rows'][10]['HP_cycle']+1)))
check('AI_return_forbidden',lambda:rejects(lambda f:f[1]['counts_epoch']['HC0'].update(R=1)))
check('functional_79_mask_still_forbidden',lambda:need(c.MANDATORY_MASK>>79&1))

# Exercise the repaired live monitor parser against the actual saved second cut.
raw=actual['raw_snapshot']
class ReplayIO:
    def read(self,off):
        if off in (c.MON,c.MON+4,c.MON+8,c.MON+12):return raw['header_after'][{c.MON:'status',c.MON+4:'abi',c.MON+8:'request',c.MON+12:'response'}[off]]
        if c.MON+0x40<=off<=c.MON+0x1dc:return raw['words'][(off-c.MON-0x40)//4]
        if c.MON+0x14<=off<=c.MON+0x3c:return raw['boot_words'][(off-c.MON-0x14)//4]
        if c.MON+0x1e0<=off<=c.MON+0x1fc:return raw['boot_words'][11+(off-c.MON-0x1e0)//4]
        if 0x600<=off<0x800:return raw['release_words'][(off-0x600)//4]
        raise AssertionError('Unexpected replay offset')
class Log:
    def save(self,*a,**kw):pass
saved=c.wait_command;c.wait_command=lambda *a,**kw:raw['header_after']
try:
    check('live_parser_accepts_actual_second_cut_without_reissuing',lambda:need(c.monitor_finish(ReplayIO(),Log(),2)['generation']==4))
    def reject_wrong_freeze():
        original=raw['release_words'][7];raw['release_words'][7]=1
        try:
            try:c.monitor_finish(ReplayIO(),Log(),2)
            except RuntimeError:return
            raise AssertionError('Wrong FREEZE accepted')
        finally:raw['release_words'][7]=original
    check('live_parser_still_rejects_stale_FREEZE1',reject_wrong_freeze)
finally:c.wait_command=saved

spec=importlib.util.spec_from_file_location('continuation_parent',D/'ps_release_board.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Support:
    def need(self,ok,why):
        if not ok:raise RuntimeError(why)
    def boot_id(self):return before['boot_id']
    def read_json(self,p):return read(p)
    def digest(self,p):return hashlib.sha256(p.read_bytes()).hexdigest()
    def save_new(self,p,v):
        with p.open('x') as f:json.dump(v,f)
fixture_dir=W/('offline-continuation-'+uuid.uuid4().hex)
fixture_dir.mkdir()
with contextlib.nullcontext(str(fixture_dir)) as name:
    base=Path(name);(base/'metadata').mkdir();(base/'run-1/consume/capture').mkdir(parents=True)
    payload=(run/'consume/capture/raw.jsonl').read_bytes();(base/'run-1/consume/capture/raw.jsonl').write_bytes(payload)
    stop=read(E/'board-candidate/metadata/stopped.json');(base/'metadata/stopped.json').write_text(json.dumps(stop))
    m.BASE=base;m.ROOT_META=base/'metadata';m.b=Support();m.cfg=dict(same_boot_continuation=dict(approved=True,boot_id=before['boot_id']))
    check('original_stop_blocks_without_resolution',lambda:need(m.stopped()))
    receipt=dict(valid=True,boot_id=before['boot_id'],original_failure_preserved=True,MMIO_commands=0,original_raw_sha256=hashlib.sha256(payload).hexdigest())
    (base/'metadata/consume-parser-resolution.json').write_text(json.dumps(receipt))
    check('explicit_parser_resolution_preserves_original_stop',lambda:need(not m.stopped() and read(base/'metadata/stopped.json')==stop))
    m.mark_stopped('checker-rearm',1,dict(error='offline error'))
    check('new_failure_latches_separately_and_cannot_resume',lambda:need(m.stopped() and (base/'metadata/diagnostic-continuation-stopped.json').exists() and read(base/'metadata/stopped.json')==stop))
    m.authorize=lambda:None
    def forbidden(stage):
        try:m.main(stage,1)
        except RuntimeError:return
        raise AssertionError('New hardware action permitted')
    for stage in ('install','candidate-reboot','consume','observe-before'):
        check('continuation_forbids_'+stage,lambda stage=stage:forbidden(stage))

report=dict(offline_only=True,MMIO=0,SDK=0,total=len(cases),passed=sum(x['passed'] for x in cases),cases=cases,actual_saved_gate=gate)
(D/'offline-tests.json').write_text(json.dumps(report,indent=2)+'\n')
for x in cases:
    if not x['passed']:print(x)
print('OFFLINE_CONTINUATION_TESTS',report['passed'],'/',report['total'])
assert report['passed']==report['total']
