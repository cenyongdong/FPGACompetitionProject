"""Root orchestration of the human-approved R9 package.

Revalidate all 114 recorded local evidence hashes and real artifacts at each
entry. Reuse the already evaluated offline qualification; never reimplement
BOOT/SDK/UART/process logic. Real runtime state and human receipt stay live.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,sys,time
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[3];S=Path(__file__).parent
E=R/'tools/pose-v1/evidence/hdmi-live-20261018-r9'
G=E/'remote-read-v3-sources-r9r1';A=E/'startup-authorization-r9.json'
STATE=R/'tools/pose-v1/evidence/hdmi-live-20261017-r3/continuation-state.json'
MAN=E/'controlled-startup-read-v3-execution-r9/manifest.json'
MH='3b5887ecece138973ee2ebef20b533211971674c0b33c7cbd9784159065cf085'
RH='ccfc5ee31dc51f09493c64ce9d82102a279bc51bc312074eb0793404e79bd704'
def need(x,msg):
    if not x:raise ValueError(msg)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_bytes())
HP=S/'controlled_read_v3_r9.py'
need(sha(HP)=='c39773c4dab9d72877abbe5114088fd45a91438473335ea7f26c0d1cbf3f72ea','Actual Host changed')
spec=importlib.util.spec_from_file_location('r9_root_bound_host',HP)
host=importlib.util.module_from_spec(spec);exec(compile(HP.read_bytes(),str(HP),'exec'),vars(host))
manifest=load(MAN);context=manifest['execution_context'];cfg=load(G/'configuration.json')
review=load(G/'local-review.json');sm=load(G/'source-manifest.json')
need(sha(MAN)==MH and cfg['manifest_sha256']==sm['manifest_sha256']==MH
     and cfg['local_review_sha256']==sm['local_review_sha256']==review['local_review_sha256']==RH,
     'Actual package/source/local-review binding differs')
need(review==load(E/'host-plan-review-r1/stdout.json')['manifest_review'],'Generated complete review differs')
gen=host.adapter('generator');backend=host.adapter('executor')
RUN=E/'runtime-root-r2'
RUN.mkdir(exist_ok=True)
backend.EVIDENCE=RUN
original_imported=backend.imported
def transport_import(name,path):
    loaded=original_imported(name,path)
    if Path(path).resolve()==(S/'secure_transport_read_v3_r9.py').resolve():
        need(loaded.backend.HOST=='root@192.168.126.49'
             and loaded.backend.REMOTE=='/root/hdmi-live-20261018-r9/',
             'Actual public transport target changed')
        return loaded.backend
    return loaded
backend.imported=transport_import
original_operation=backend.operation
def operation(name):
    if name in ['publish-failure-evidence','stage-fallback-preflight']:
        name+='-r2'
    mapped=name.replace('_','-underscore-')
    need(mapped.replace('-underscore-','_')==name,'Local operation mapping is not reversible')
    return original_operation(mapped)
backend.operation=operation


ledger={}
for key,value in review['local_evidence_sha256'].items():
    path=Path(key)
    if key.startswith('execution-adapter/'):
        path=Path(context['adapters'][key.split('/',1)[1]]['path'])
    elif not path.is_absolute():path=E/path
    need(path.is_file() and sha(path)==value,'Recorded qualification evidence changed: '+str(path))
    ledger[str(path.resolve())]=value
for path,value in context['source_closure'].items():
    need(path not in ledger or ledger[path]==value,'Source ledger conflict')
    ledger[path]=value
for name,item in manifest['files'].items():ledger[str(MAN.parent/name)]=item['sha256']
ledger[str(MAN)]=MH
for name in ['configuration.json','local-review.json','source-manifest.json']:
    ledger[str(G/name)]=sha(G/name)
for stage,row in sm['stages'].items():ledger[str(G/row['name'])]=row['sha256']
# Source/library values already signed by the accepted formal review remain fixed.
formal=load(E/'read-v3r9-independent-reports-r1/review.json')
for name,value in formal['source_sha256'].items():
    ledger[str(R/'.local/hdmi-live-20261018-r9/reference'/name)]=value

def gate(action=None):
    live=load(STATE)
    need(not live['whole_task_pause']['paused'] and not str(live['status']).startswith('paused'), 'Current task paused')
    need(live['old_DATA']=='paused','Old DATA protection changed')
    if action in {'install_candidate','uart_candidate','candidate_reboot','shared_three','uart_fallback','original_fallback_reboot'}:
        need(live['onsite_observation_work']['paused'] is False,'Current onsite observation paused')
    for path,value in ledger.items():need(sha(path)==value,'Bound qualification/artifact/source changed: '+path)
    auth=load(A)
    need(auth.get('approved') is True and auth.get('active') is True and auth.get('approved_by')=='user'
         and auth.get('package_id')=='ai-read-v3' and auth.get('manifest_sha256')==MH
         and auth.get('local_review_sha256')==RH and bool(auth.get('user_confirmation'))
         and auth.get('caps')==cfg['caps'] and auth.get('old_DATA')=='paused'
         and auth.get('filesystem_repair') is False,'Actual new authorization changed/absent')
    need(action is None or action in auth['allowed_actions'],'Action not authorized: '+str(action))
    return auth

def entry(stage,generation_dir,approved,receipt):
    need(Path(generation_dir).resolve()==G.resolve() and approved is True and Path(receipt).resolve()==A.resolve(),
         'Actual fixed source/approval entry differs')
    row=sm['stages'][stage];gate(gen.STAGES[stage])
    path=G/row['name']
    need(row['action']==gen.STAGES[stage] and path.read_bytes()==gen.render_stage(cfg,stage).encode(),
         'Complete actual remote stage rendering changed')
    return gen,cfg,review,dict(stage=stage,source=str(path),source_sha256=row['sha256'],
        manifest_sha256=MH,local_review_sha256=RH,authorized_for_exact_stage_entry=True,remote_actions_executed=False)

def configuration():
    gate();return gen,cfg,review
backend.entry=entry;backend.configuration=configuration
gen.actual_configuration=lambda:(cfg,review)

def startup():
    module=host.adapter('startup_controller')
    module.EVIDENCE=RUN
    module.capture_dir=lambda kind:RUN/('uart-'+kind+'-read-v3-r2')
    module.transport=lambda code,out,seconds:backend.transport_bounded(code,out,seconds,seconds)
    module.configuration=configuration
    def approval(action,approved,receipt):
        need(approved is True and Path(receipt).resolve()==A.resolve(),'Actual startup receipt absent')
        gate(action);return gen,cfg,review
    module.approval=approval
    original=module.capture_source
    def capture_source(configuration,kind,receipt):
        raw=original(configuration,kind,receipt)
        old=str(RUN/'controlled-startup-read-v3/manifest.json')
        need(raw.count(old)==1,'Frozen UART manifest literal differs')
        actual=raw.replace(old,str(MAN))
        need(actual.replace(str(MAN),old)==raw,'UART exact manifest binding inverse differs')
        prefix = ("$ErrorActionPreference = 'Stop'\n"
                  "Import-Module 'C:/Windows/System32/WindowsPowerShell/v1.0/Modules/Microsoft.PowerShell.Utility/Microsoft.PowerShell.Utility.psd1' -Force\n"
                  "Import-Module 'C:/Windows/System32/WindowsPowerShell/v1.0/Modules/CimCmdlets/CimCmdlets.psd1' -Force\n")
        return prefix+actual
    module.capture_source=capture_source
    return module

def verify_actual_reboot_source(directory):
    recorded=(directory/'remote-code.py').read_bytes()
    sent=(directory/'stdin-source.py').read_bytes()
    expected=startup().reboot_source(gen,cfg,'candidate').encode('utf-8')
    need(sent==expected and b'\r' not in sent and recorded==sent.replace(b'\n',b'\r\n'),
         'Actual reboot stdin differs from full reviewed rendering or exact Windows newline log')
    proof=dict(actual_stdin_SHA256=hashlib.sha256(sent).hexdigest(),
        recorded_log_SHA256=hashlib.sha256(recorded).hexdigest(),exact_full_rendered_source=True,
        exact_reversible_Windows_log_newlines=True,original_files_not_changed=True)
    target=RUN/'actual-reboot-source-newline-proof.json'
    if target.exists():need(load(target)==proof,'Reboot source proof changed')
    else:target.write_text(json.dumps(proof,indent=2)+'\n')
    return True

def bind_publish_source_proof():
    import ast,copy
    source=host.BASES['executor'][0]
    need(sha(source)==host.BASES['executor'][1],'Original publish algorithm changed')
    tree=ast.parse(source.read_bytes())
    original=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='publish')
    actual=copy.deepcopy(original)
    call=next(n for n in ast.walk(actual) if isinstance(n,ast.Call) and len(n.args)==2
              and isinstance(n.args[1],ast.Constant) and n.args[1].value=='Actual reboot stdin source differs')
    saved=copy.deepcopy(call.args[0])
    call.args[0]=ast.parse('verify_actual_reboot_source(directory)',mode='eval').body
    failure_loop=next(n for n in ast.walk(actual) if isinstance(n,ast.For)
        and isinstance(n.target,ast.Tuple) and len(n.target.elts)==2
        and isinstance(n.target.elts[0],ast.Name) and n.target.elts[0].id=='name'
        and isinstance(n.target.elts[1],ast.Name) and n.target.elts[1].id=='row')
    names=[n for n in ast.walk(failure_loop) if isinstance(n,ast.Name) and n.id=='name']
    need(len(names)==2,'Original failure loop name uses differ')
    for node in names:node.id='failure_relative_name'
    reverse=copy.deepcopy(actual)
    reversed_loop=next(n for n in ast.walk(reverse) if isinstance(n,ast.For)
        and isinstance(n.target,ast.Tuple) and isinstance(n.target.elts[0],ast.Name)
        and n.target.elts[0].id=='failure_relative_name')
    for node in ast.walk(reversed_loop):
        if isinstance(node,ast.Name) and node.id=='failure_relative_name':node.id='name'

    reverted=next(n for n in ast.walk(reverse) if isinstance(n,ast.Call) and len(n.args)==2
                  and isinstance(n.args[1],ast.Constant) and n.args[1].value=='Actual reboot stdin source differs')
    reverted.args[0]=saved
    need(ast.dump(reverse,include_attributes=False)==ast.dump(original,include_attributes=False),
         'Complete publish proof inverse AST differs')
    ast.fix_missing_locations(actual)
    backend.verify_actual_reboot_source=verify_actual_reboot_source
    exec(compile(ast.Module(body=[actual],type_ignores=[]),str(source)+' [exact actual stdin/log proof]', 'exec'),backend.__dict__)

bind_publish_source_proof()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['preflight','bootstrap','prepare','put-all','put-remaining','verify-package','get-original',
        'verify-original','publish-host-copy','capture-candidate','install','reboot-candidate','publish-candidate-startup',
        'postboot-restore','probe','get-failure','publish-failure','publish-fallback-preflight','get-probe','verify-probe','publish-probe-review','shared','fallback-preflight','capture-fallback','reboot-fallback'])
    args=parser.parse_args();op=args.operation
    out=RUN/'root-orchestration'/(op+'-r2' if op.startswith('capture-') or op in ['publish-candidate-startup','publish-failure','fallback-preflight'] else op);out.mkdir(parents=True,exist_ok=False)
    (out/'actual-root-controller.py').write_bytes(Path(__file__).read_bytes())
    (out/'entry-contract.json').write_text(json.dumps(dict(approved_manifest_SHA256=MH,local_review_SHA256=RH,
        revalidated_file_count=len(ledger),actual_114_item_review_reused=True,
        numerical_SDK_BOOT_process_algorithms_unchanged=True,
        runtime_pause_and_human_approval_rechecked_before_each_action=True),indent=2)+'\n')
    started=time.monotonic();success=False
    try:
        gate()
        if op in ['probe','shared']:
            need(not load(STATE).get('r9_runtime',{}).get('sdk_loads_stopped',False),'SDK failure stop active; no new loads')
        if op in ['preflight','prepare','verify-package','install','postboot-restore','probe','shared','fallback-preflight']:
            value=backend.run_stage(op,G,True,A)
        elif op=='bootstrap':value=backend.bootstrap(G,RUN/'read-v3-execution/stage-preflight/stage-result.json',True,A)
        elif op in ['put-all','put-remaining']:
            value={}
            for name in cfg['files']:
                if name=='BOOT-original.bin':continue
                if op=='put-remaining' and name=='BOOT-ai-read-v3.bin':
                    existing=load(RUN/'read-v3-execution/put-BOOT-ai-read-v3.bin/transfer-result.json')
                    need(existing['passed'] and existing['sha256']==cfg['files'][name]['sha256']
                         and existing['manifest_sha256']==MH and existing['local_review_sha256']==RH,
                         'Prior completed BOOT transfer not qualified')
                    value[name]=dict(completed_transfer_reused=True,actual_receipt=existing)
                    continue

                value[name]=backend.artifact_transfer(name,G,True,A)
                print(json.dumps(dict(transferred=name,passed=True)),flush=True)
        elif op=='get-original':value=backend.get_evidence('package/BOOT-original.readback.bin',G,True,A)
        elif op=='get-failure':
            import shutil
            terminal=load(RUN/'read-v3-execution/stage-probe/stage-result.json')
            child=terminal['result']
            need(child['child_exit']==71 and child['timeout'] is False and child['child_still_running'] is False,
                 'Actual failed terminal state differs')
            target=RUN/'failure-return';target.mkdir()
            returned={}
            for name in ['metadata/probe.result.json','dma-read-v3.trace.jsonl',
                         'dma-read-v3.trace.jsonl.64.source.bin','dma-read-v3.trace.jsonl.64.actual.bin']:
                actual=backend.get_evidence(name,G,True,A)
                destination=target/name;destination.parent.mkdir(exist_ok=True)
                shutil.copyfile(actual['local_path'],destination)
                need(sha(destination)==actual['sha256'],'Complete failed-probe return copy differs')
                returned[name]=dict(bytes=actual['bytes'],sha256=actual['sha256'])
                print(json.dumps(dict(preserved=name,passed=True)),flush=True)
            for name,field in [('probe.stdout.txt','stdout'),('probe.stderr.txt','stderr')]:
                data=child[field].encode('utf-8');row=child['files'][name]
                need(len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],
                     'Captured full child output does not reproduce exact remote bytes')
                (target/name).write_bytes(data);returned[name]=row
            for name,row in child['files'].items():
                need(name in returned and returned[name]==row,'Failed evidence member missing or changed')
            value=dict(preserved=True,package_id=cfg['package_id'],manifest_sha256=MH,local_review_sha256=RH,
                boot_id=child['boot_id'],files=returned,failed_stage='probe',child_exit=71,
                actual_stage_exit=terminal['stage_exit'],SDK_error_not_retried=True,
                larger_DMA_and_shared_stopped=True,returned_root=str(target))
            (RUN/'failure-evidence-review-r9.json').write_text(json.dumps(value,indent=2)+'\n')
        elif op=='publish-failure':
            value=backend.publish('failure-evidence',RUN/'failure-evidence-review-r9.json',G,True,A,
                                  dict(returned_root=str(RUN/'failure-return')))
        elif op=='publish-fallback-preflight':
            actual_path=RUN/'read-v3-execution/stage-fallback-preflight-r2/stage-result.json'
            actual=load(actual_path);source=RUN/'fallback-preflight-receipt-r9.json'
            source.write_text(json.dumps(actual['result'],indent=2)+'\n')
            value=backend.publish('fallback-preflight',source,G,True,A,dict(stage_result=str(actual_path)))
        elif op=='get-probe':
            import shutil
            target=RUN/'probe-return';target.mkdir()
            names=['metadata/probe.result.json','dma-read-v3.trace.jsonl']+[
                'dma-read-v3.trace.jsonl.'+str(size)+'.'+role+'.bin'
                for size in [64,4096,65536,1048576] for role in ['source','actual']]
            value={}
            for name in names:
                actual=backend.get_evidence(name,G,True,A)
                shutil.copyfile(actual['local_path'],target/Path(name).name)
                need(sha(target/Path(name).name)==actual['sha256'],'Complete probe return copy differs')
                value[name]=actual
                print(json.dumps(dict(returned=name,passed=True)),flush=True)
        elif op=='verify-probe':
            target=RUN/'probe-return';boot=load(RUN/'candidate-startup-read-v3/result.json')['boot_id']
            value=gen.verify_probe(target/'probe.result.json',target/'dma-read-v3.trace.jsonl',target,boot,
                                   RUN/'probe-independent-review-r9.json')
        elif op=='publish-probe-review':
            target=RUN/'probe-return';boot=load(RUN/'candidate-startup-read-v3/result.json')['boot_id']
            value=backend.publish('probe-review',RUN/'probe-independent-review-r9.json',G,True,A,
                dict(receipt=str(target/'probe.result.json'),trace=str(target/'dma-read-v3.trace.jsonl'),
                     returned_root=str(target),candidate_boot_id=boot))

        elif op=='verify-original':
            value=gen.verify_original(RUN/'read-v3-execution/get-BOOT-original.readback.bin/BOOT-original.readback.bin',
                                      RUN/'original-host-copy-review-r9.json')
        elif op=='publish-host-copy':value=backend.publish('host-copy',RUN/'original-host-copy-review-r9.json',G,True,A,dict(returned_file=str(RUN/'read-v3-execution/get-BOOT-original.readback.bin/BOOT-original.readback.bin'),get_result=str(RUN/'read-v3-execution/get-BOOT-original.readback.bin/get-result.json')))
        elif op=='publish-candidate-startup':
            value=backend.publish('candidate-startup',RUN/'candidate-startup-read-v3/result.json',G,True,A,dict(startup_directory=str(RUN/'candidate-startup-read-v3')))
        elif op.startswith('capture-'):
            value=startup().capture(op.split('-',1)[1],True,A)
        else:value=startup().reboot(op.split('-',1)[1],True,A)
        (out/'result.json').write_text(json.dumps(value,indent=2)+'\n');success=True
        print(json.dumps(dict(operation=op,passed=True,seconds=time.monotonic()-started)),flush=True)
        return 0
    finally:
        (out/'execution.json').write_text(json.dumps(dict(operation=op,success=success,seconds=time.monotonic()-started,
            actual_controller_SHA256=sha(Path(__file__)),no_automatic_retry=True),indent=2)+'\n')

if __name__=='__main__':raise SystemExit(main())
