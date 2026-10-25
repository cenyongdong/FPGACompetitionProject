"""Structural stage tests with local files and MMIO models; no board access."""
import copy
import json
from pathlib import Path
import sys
import contextlib
import os
import shutil
import uuid

sys.dont_write_bytecode = True
import r45_diagnostic_stages as stages
import offline_tests as fixtures
from capture_tests import IO

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent
c = stages.c


def save(path,value):
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream)


class Evidence:
    def __init__(self,directory):
        directory.mkdir()
        self.directory,self.events=directory,[]
    def save(self,event,**values): self.events.append(dict(event=event,**values))
    def close(self): pass


class Scenario:
    def __init__(self,run,healthy=False,fail=None):
        self.run,self.calls,self.fail=run,[],fail
        run.mkdir()
        (run/'metadata').mkdir()
        b,a,t,p,q=fixtures.fixture()
        self.boot=b['boot_id']
        words=[0]*104
        words[0],words[83]=0x41495201,3<<14
        self.before=dict(valid=True,boot_id=self.boot,normalized=b,raw_snapshot=dict(words=words))
        self.after=dict(valid=True,boot_id=self.boot,normalized=a)
        self.pb,self.pa=p,q
        first=fixtures.load(fixtures.R44/'cycletrace/raw.decoded.json')
        first['boot_id']=self.boot
        first['banks'][1]=dict(bank=1,published=False,fired=False)
        for row in first['banks'][0]['rows']: row['drain_state']=0
        self.trace_before=first
        rows=t['rows']
        arm=t['arm_HP_cycle']
        # Descriptor-complete derived 32-pre / 95-post model. Original r38/r44
        # files remain unchanged; these constructed samples are not board data.
        first_row=rows[0]
        leading=[dict(first_row,HP_cycle=arm+k) for k in range(-32,-8)]
        tail=[dict(rows[-1],HP_cycle=arm+k) for k in range(rows[-1]['HP_cycle']-arm+1,96)]
        rows=leading+rows+tail
        assert len(rows)==128
        self.trace_after=dict(boot_id=self.boot,status=15,banks=[first['banks'][0],
             dict(bank=1,published=True,count=128,trigger_index=32,trigger_cycle=arm,rows=rows)])
        control=copy.deepcopy(a['control'])
        control.update(request=7,response=7,rearm_used=True,rearm_issued=True,full_PC_status=0)
        self.postclear=dict(valid=True,boot_id=self.boot,normalized=dict(valid=True,boot_id=self.boot,
             checker_ready_for_SDK=True,control=control))
        if healthy:
            b['counts_lifetime']['PS']['R']=0
            b['first_RVALID_HP_cycle']=None
            b['control']['full_PC_status']=0
            for ch in ('PS','S01'):
                b['levels'][ch+'_RVALID']=False
                b['pins'][ch]['RVALID']=False
            self.trace_before.update(status=0,banks=[dict(bank=0,published=False,fired=False),
                                                    dict(bank=1,published=False,fired=False)])
            self.pb=dict(boot_id=self.boot,status=60,published=False,fired=False,
                         live_flags=dict(PS_HP2_resetn=True,PC_system_resetn=True,
                                         PC_checker_ready=True,PC_seen_reset_low=True))

    def spawn(self,name,argv_fn):
        out=self.run/name
        out.mkdir()
        argv=argv_fn(out)
        self.calls.append(dict(name=name,argv=argv))
        assert argv[0]==sys.executable
        if name==self.fail:return out,2
        if name in ('observe-before','consume','checker-rearm'):
            assert argv[3]==str(out/'capture') and not (out/'capture').exists()
            (out/'capture').mkdir()
            record={'observe-before':self.before,'consume':self.after,'checker-rearm':self.postclear}[name]
            save(out/'capture/result.json',record)
        else:
            assert argv[2]==str(out/'raw.json')
            record={'cycletrace-before':self.trace_before,'cycletrace-after':self.trace_after,
                    'protocol-before':self.pb,'protocol-after':self.pa}[name]
            save(out/'raw.json',dict(offline_placeholder_only=True,boot_id=self.boot))
            save(out/'raw.decoded.json',record)
        return out,0

    def stage(self,name):
        c.runtime=lambda:self.boot
        c.owners=lambda:[]
        return stages.diagnostic_stage(name,self.run,PACKAGE,self.boot,self.spawn)

    def prefix(self):
        return [self.stage(n) for n in ('observe-before','cycletrace-before','protocol-before','before-seed')]


def main():
    cases=[]
    def check(name,action):
        try: action();cases.append(dict(name=name,passed=True))
        except Exception as error:cases.append(dict(name=name,passed=False,error=str(error)))
    c.fresh_json=save
    c.Evidence=Evidence
    c.time.sleep=lambda seconds:None
    original_mkdir=Path.mkdir
    if os.name=='nt':
        # The sandbox's Windows token cannot reopen Python 3.13's user-only
        # 0700 ACL. Production board Linux retains its original modes.
        Path.mkdir=lambda self,mode=0o777,parents=False,exist_ok=False:original_mkdir(
            self,mode=0o777,parents=parents,exist_ok=exist_ok)

    @contextlib.contextmanager
    def local_temporary_directory():
        root=HERE/('offline-stages-'+uuid.uuid4().hex)
        root.mkdir()
        try:yield root
        finally:
            assert root.resolve().parent==HERE.resolve()
            shutil.rmtree(str(root))

    with local_temporary_directory() as tmp:
        root=Path(tmp)
        full=Scenario(root/'complete')
        def known_chain():
            result=full.prefix()
            assert all(x['valid'] for x in result),result
            assert result[-1]['eligible'] and not (full.run/'metadata/observe.json').exists()
            for name in ('consume','cycletrace-after','protocol-after','consumed-gate'):
                row=full.stage(name)
                assert row['valid'],row
            assert not (full.run/'metadata/sdk-ready.json').exists()
            before_bytes=(full.run/'observe-before/capture/result.json').read_bytes()
            protocol_bytes=(full.run/'protocol-before/raw.decoded.json').read_bytes()
            row=full.stage('checker-rearm')
            assert row['valid'] and row['SDK_admitted'],row
            observe=json.loads((full.run/'metadata/observe.json').read_text())
            assert (observe['boot_id']==full.boot and observe['discard_probe_admissible'] and
                    observe['S01_source_connected_confirmed'] and observe['S01_source_input_mask']==3<<14)
            assert before_bytes==(full.run/'observe-before/capture/result.json').read_bytes()
            assert protocol_bytes==(full.run/'protocol-before/raw.decoded.json').read_bytes()
        check('known_chain_preserves_original_before_and_admits_after_CHKR_only',known_chain)

        def duplicate_stage():
            count=len(full.calls)
            try:full.stage('consume')
            except RuntimeError:pass
            else:raise AssertionError('duplicate stage accepted')
            assert len(full.calls)==count
        check('repeated_stage_refused_without_child',duplicate_stage)

        io=IO()
        io.consumed=io.cleared=io.arm_issued=io.rearm_issued=True
        io.control_seq=7
        io.monitor_seq=12
        io.held_control=io.control_words()
        c.MMIO=lambda evidence,boot_id:io
        io.close=lambda:None
        def post_checks():
            assert full.stage('post-frame-protocol')['valid']
            assert full.stage('post-joint-protocol')['valid']
            assert io.writes==[(c.CTRL,c.SNAP),(c.CTRL,c.SNAP)] and io.monitor_seq==12
        check('post_frame_and_joint_one_SNAP_each_zero_monitor_commands',post_checks)

        def healthy_no_consume():
            scenario=Scenario(root/'healthy',healthy=True)
            result=scenario.prefix()
            assert all(x['valid'] for x in result),result
            assert result[-1]['classification']=='healthy_no_target' and result[-1]['continue_allowed']
            count=len(scenario.calls)
            denied=scenario.stage('consume')
            assert not denied['valid'] and len(scenario.calls)==count
            assert not (scenario.run/'metadata/sdk-ready.json').exists()
        check('healthy_status0_unpublished_banks_do_not_trigger_consume',healthy_no_consume)

        def failed_child():
            scenario=Scenario(root/'failed',fail='observe-before')
            result=scenario.stage('observe-before')
            assert not result['valid'] and result['exit_code']==2 and len(scenario.calls)==1
            assert not (scenario.run/'metadata/observe.json').exists()
        check('collector_failure_saved_without_retry_or_SDK_metadata',failed_child)

        def wrong_boot():
            scenario=Scenario(root/'wrong-boot')
            c.runtime=lambda:'another-boot'
            c.owners=lambda:[]
            try:stages.diagnostic_stage('observe-before',scenario.run,PACKAGE,scenario.boot,scenario.spawn)
            except RuntimeError:pass
            else:raise AssertionError('wrong boot accepted')
            assert not scenario.calls
        check('boot_guard_prevents_child',wrong_boot)

        def wrong_native_status():
            scenario=Scenario(root/'native-error')
            for name in ('observe-before','cycletrace-before','protocol-before','before-seed',
                         'consume','cycletrace-after','protocol-after','consumed-gate','checker-rearm'):
                assert scenario.stage(name)['valid']
            bad=IO()
            bad.consumed=bad.cleared=bad.arm_issued=bad.rearm_issued=True
            bad.control_seq=7
            bad.held_control=bad.control_words()
            original=bad.control_words
            def words():
                value=original()
                value[6+58//32] |= 1<<(58%32)
                return value
            bad.control_words=words
            bad.close=lambda:None
            c.MMIO=lambda evidence,boot_id:bad
            result=scenario.stage('post-frame-protocol')
            assert not result['valid'] and 58 in result['status_bits']
            assert bad.writes==[(c.CTRL,c.SNAP)] and bad.monitor_seq==8
            assert (scenario.run/'post-frame-protocol/result.json').exists()
        check('fresh_rule_failure_retains_full160_and_never_retries',wrong_native_status)

    report=dict(offline_structural_models_only=True,board_test_pass_claimed=False,
                total=len(cases),passed=sum(x['passed'] for x in cases),cases=cases)
    (HERE/'stage-tests.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    for case in cases:
        if not case['passed']:print(case)
    assert report['passed']==report['total']
    print('OFFLINE_STAGE_TESTS',report['passed'],'/',report['total'],'NO_BOARD_PASS_CLAIM')


if __name__=='__main__':main()
