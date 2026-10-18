"""Pure r6 identity adapters and actual post-route evidence gate; no tool launch."""
from pathlib import Path
import ast
import copy
import hashlib
import importlib.util
import json
import re
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[3]
E=ROOT/'tools/pose-v1/evidence/hdmi-live-20261017-r3'
REF=ROOT/'.local/hdmi-live-20261017-r3/reference'
DRIVER=E/'postroute-driver-preparation-r4/r6-driver.py'
DRIVER_SHA='9a71988ec49350e516ac0ceb4d6d638b3c732a50561901a68e5d9899284e99d4'
R5_DRIVER=Path(__file__).with_name('continue_ai_read_checkpoint.py')
R5_DRIVER_SHA='ee11b66896bb84886b186a4667fd4d5c871ec7c404bcc034e56637bacd01504b'
PHYSOPT_SHA='f58a5f8e6f432be7e656de5ee32eae5ae63b491d5a5cb1055425ee32895525d9'
ORIGINAL_NATIVE_SHA='fe2a27e53a4131a1503d5e28dea02a79dceaef954d56bf3912a56b642a91269a'
PARAMETERS=['-placement_opt','-routing_opt','-rewire','-critical_pin_opt']
ORDER=['original_route_design_NoTimingRelaxation','four_option_postroute_phys_opt',
       'first_complete_original_JFM_route_post','original_checkpoint_and_native_reports']


def need(okay,message):
    if not okay:raise ValueError(message)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save_new(path,value):
    with Path(path).open('x',encoding='utf-8') as stream:
        json.dump(value,stream,indent=2,ensure_ascii=False);stream.write('\n')


def adapt_frozen(path,expected,changes,adapter_path):
    """Only explicitly named Constant nodes may change; prove full AST inverse."""
    path=Path(path);adapter_path=Path(adapter_path)
    raw=path.read_bytes();need(hashlib.sha256(raw).hexdigest()==expected,'Frozen algorithm source changed')
    original=ast.parse(raw,filename=str(path));tree=copy.deepcopy(original)
    by_position={(line,column):(old,new) for line,column,old,new in changes}
    need(len(by_position)==len(changes),'Duplicate AST replacement position')
    replaced=[]
    for node in ast.walk(tree):
        position=(getattr(node,'lineno',None),getattr(node,'col_offset',None))
        if isinstance(node,ast.Constant) and position in by_position:
            old,new=by_position[position]
            need(isinstance(node,ast.Constant) and type(node.value) is str and node.value==old,
                 'Frozen AST replacement location/value changed')
            node.value=new;replaced.append(position)
    need(set(replaced)==set(by_position),'An exact AST replacement was not applied')
    inverse=copy.deepcopy(tree)
    for node in ast.walk(inverse):
        position=(getattr(node,'lineno',None),getattr(node,'col_offset',None))
        if isinstance(node,ast.Constant) and position in by_position:node.value=by_position[position][0]
    original_dump=ast.dump(original,include_attributes=False)
    need(ast.dump(inverse,include_attributes=False)==original_dump,'Inverse AST differs from frozen full algorithm')
    adapted_dump=ast.dump(tree,include_attributes=False)
    proof={'base_source_path':str(path.resolve()),'base_source_sha256':expected,
           'actual_adapter_path':str(adapter_path.resolve()),'actual_adapter_sha256':sha(adapter_path),
           'effective___file__':str(path.resolve()),'compile_filename':str(path)+' [r6 explicit identity AST]',
           'changes':[{'line':a,'column':b,'old':c,'new':d} for a,b,c,d in changes],
           'replacement_count':len(replaced),'inverse_full_AST_equal':True,
           'original_AST_sha256':hashlib.sha256(original_dump.encode()).hexdigest(),
           'adapted_AST_sha256':hashlib.sha256(adapted_dump.encode()).hexdigest()}
    namespace={'__name__':'read_r6_frozen_algorithms','__file__':str(path.resolve())}
    exec(compile(tree,proof['compile_filename'],'exec'),namespace)
    module=SimpleNamespace(**namespace)
    module.execution_namespace=namespace
    return module,proof,raw,ast.unparse(tree).encode('utf-8')


def driver():
    need(sha(DRIVER)==DRIVER_SHA and sha(R5_DRIVER)==R5_DRIVER_SHA,'Frozen r6/r5 physical driver identity differs')
    spec=importlib.util.spec_from_file_location('frozen_r6_public_pure_contract',DRIVER)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    # Frozen bytes stay in their real archive. These explicit filesystem
    # bindings are only for the three public pure functions, never main/EDA.
    module.OLD_NATIVE=E/'checkpoints-before-route-r4/ai7030_edif_top.tcl'
    module.SOURCE_DRIVER=R5_DRIVER
    module.NATIVE=REF/'fpai_demo_vivado.runs/route_read_v3r6'
    module.CHECKPOINT=E/'checkpoints-before-route-r4/ai7030_edif_top_physopt.dcp'
    module.E=E
    return module


def verify_phase_driver(directory,mode,evidence):
    """Freeze each real phase source; permit only unchanged optimizer ASTs."""
    path=directory/'actual-driver.py';actual=ast.parse(path.read_bytes());frozen=ast.parse(DRIVER.read_bytes())
    names={'postroute_transform','postroute_configuration','verify_postroute_runtime','substitutions'}
    def functions(tree):
        return {node.name:ast.dump(node,include_attributes=False) for node in tree.body
                if isinstance(node,ast.FunctionDef) and node.name in names}
    need(functions(actual)==functions(frozen) and set(functions(actual))==names,
         'Actual phase changed the frozen optimization algorithm: '+mode)
    native=REF/'fpai_demo_vivado.runs/route_read_v3r6'
    owner_path=native/('bootstrap-owner.json' if mode=='bootstrap' else mode+'-owner.json')
    owner=load(owner_path)
    need(owner.get('driver_SHA256')==sha(path),'Actual phase driver/owned source SHA differs: '+mode)
    evidence[str(path)]=sha(path);evidence[str(owner_path)]=sha(owner_path)


def verify_optimizer(evidence=None):
    """Require original route -> one exact optimizer -> first complete JFM hook."""
    evidence={} if evidence is None else evidence
    physical=E/'checkpoints-before-route-r4/ai7030_edif_top_physopt.dcp'
    need(physical.stat().st_size==44506212 and sha(physical)==PHYSOPT_SHA,'Frozen r4 physical checkpoint differs')
    rejection_path=E/'route-release-rejection-r5/execution.json';rejection=load(rejection_path)
    need(rejection.get('exit')==1 and rejection.get('bit_generation_prerequisite_pass') is False and
         rejection.get('formal_review_file_created') is False and
         rejection.get('new_timing_or_DRC_waiver') is False,'Actual r5 formal timing rejection must remain preserved')
    implementation=driver()
    need(sha(implementation.OLD_NATIVE)==ORIGINAL_NATIVE_SHA,'Frozen complete original native source changed')
    expected=implementation.postroute_configuration()
    need(expected.get('parameters')==PARAMETERS and expected.get('order')==ORDER and
         Path(expected.get('source_driver_path','')).resolve()==R5_DRIVER.resolve() and
         expected.get('source_driver_SHA256')==R5_DRIVER_SHA and
         all(expected.get(key) is True for key in ('no_additional_route_pass','no_retime','no_clock_opt',
             'JFM_route_post_first_complete_call_after_optimization','timing_constraints_frequencies_DRC_profile_unchanged')) and
         expected.get('protected_source_count')==937 and expected.get('installed_file_count')==41 and
         expected.get('physical_implementation_change') is True and
         expected.get('RTL_and_external_interface_change') is False and
         expected.get('new_DRC_or_timing_waiver') is False and
         all(expected.get('inverse_transform',{}).get(key) is True for key in
             ('inverse_exact_original_named_route','inverse_exact_complete_frozen_native_bytes')),
         'Exact four-option/first-JFM/inverse optimization contract differs')
    for mode in ('bootstrap','route','reports'):
        directory=E/('read-v3r6-'+mode)
        execution=load(directory/'execution.json');phase=load(directory/'phase-review.json')
        need(type(execution.get('exit')) is int and execution['exit']==0 and
             not execution.get('timeout',False) and not execution.get('stopped_by_monitor',False) and
             phase.get('passed') is True and phase.get('mode')==mode,
             'Actual r6 phase failed/incomplete: '+mode)
        proof=load(directory/'input-proof.json')
        need(proof.get('postroute_optimization')==expected and
             proof.get('checkpoint_SHA256')==PHYSOPT_SHA and proof.get('hardware_change') is False and
             proof.get('new_timing_or_DRC_waiver') is False and
             proof.get('route_block_SHA256')==expected['inverse_transform']['optimized_route_SHA256'],
             'Actual r6 complete optimization input contract differs: '+mode)
        verify_phase_driver(directory,mode,evidence)
        for name in ('execution.json','phase-review.json','input-proof.json','actual-driver.py'):
            path=directory/name;evidence[str(path)]=sha(path)
    route=E/'read-v3r6-route'
    runtime=implementation.verify_postroute_runtime(route)
    need(load(route/'phase-review.json').get('postroute_order_checks')==runtime,
         'Actual phase runtime proof differs from raw order/status')
    native_text=implementation.OLD_NATIVE.read_text()
    original='start_step route_design\n'+native_text.split('\nstart_step route_design\n',1)[1]
    optimized,_=implementation.postroute_transform(original.replace('impl_read_v3r4','route_read_v3r6'))
    optimized=implementation.substitutions(optimized).replace('@@OUT@@',route.as_posix()).replace('@@REF@@',REF.as_posix())
    actual=(route/'stage.tcl').read_text()
    physical_commands=[line.strip() for line in actual.splitlines()
                       if re.match(r'^\s*(?:route_design|phys_opt_design|place_design|opt_design)\b',line)]
    need(actual.count(optimized)==1 and physical_commands==[
             'route_design -directive NoTimingRelaxation',
             'phys_opt_design -placement_opt -routing_opt -rewire -critical_pin_opt'] and
         len(re.findall(r'^\s*source\s+[^\n]*implementation_route_post\.tcl[^\n]*$',actual,re.MULTILINE))==1,
         'Actual r6 Tcl is not the one exact optimized route/first original hook')
    for label in ('before-opt','after-opt','after-jfm-hook'):
        report=route/('postroute-'+label+'-route-status.rpt');text=report.read_text()
        values=[]
        for key in ('routable nets','fully routed nets','nets with routing errors'):
            found=re.findall(r'# of '+key+r'\.*\s*:\s*(\d+)\s*:',text)
            need(len(found)==1,'Complete actual route-status field missing/duplicated: '+label+'/'+key)
            values.append(int(found[0]))
        need(values[0]>0 and values[0]==values[1] and values[2]==0,'Actual full route-status not fully routed/error-free: '+label)
        for path in (report,route/('postroute-'+label+'-checks.txt')):evidence[str(path)]=sha(path)
    for path in (physical,implementation.OLD_NATIVE,rejection_path,DRIVER,R5_DRIVER,route/'postroute-order.txt',route/'stage.tcl'):
        evidence[str(path)]=sha(path)
    return {'configuration':expected,'actual_runtime':runtime,'actual_evidence_sha256':dict(evidence),
            'candidate_run':'route_read_v3r6','managed_run':False,'four_option_passes':1,'first_complete_JFM_calls':1}
