"""Defer exactly the factory ICAP launcher to the separately verified stage.

The two factory output files remain raw archives and are never executed.
Unknown execution and original-source mutation retain the original rejection.
"""
import ast
import copy
from pathlib import Path

OLD = ''' foreach stem {call_procise_disable_icap procise_run_disable_icap} {
  if {[string first $stem $text]>=0} {error "BIT_RAW_DERIVED_BATCH_EXECUTION_FORBIDDEN $args"}
 }'''
NEW = ''' set expected [list cmd /c {@@REF@@/call_procise_disable_icap.bat}]
 if {$args eq $expected} {
  set f [ai_read_bit_original_open {@@OUT@@/factory-icap-deferred.txt} {WRONLY CREAT EXCL}]
  puts $f [list $args]
  close $f
  puts "AI_READ_FACTORY_ICAP_DEFERRED_TO_SEPARATE_VERIFIED_STAGE"
  return ""
 }
'''+OLD


def tcl(original, need):
    need(original.count(OLD)==1 and NEW not in original,'Frozen factory exec guard differs')
    actual=original.replace(OLD,NEW)
    need(actual.replace(NEW,OLD)==original,'Factory ICAP defer exact inverse differs')
    return actual


def verify(base, out, proof, pure=False):
    """Keep the complete original file/write/isolation proof; bind actual deferral."""
    tree=ast.parse(Path(base.__file__).read_bytes())
    original=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='bit_derived_verification')
    actual=copy.deepcopy(original)
    old_predicate=next(n for n in actual.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)
                      and n.value.args and isinstance(n.value.args[-1],ast.Constant)
                      and n.value.args[-1].value=='attempted execution of an archived raw factory entry')
    index=actual.body.index(old_predicate)
    replacement=ast.parse('''expected_attempt = "{cmd /c " + REF.as_posix() + "/call_procise_disable_icap.bat}\\n"
require((out / 'factory-exec-attempts.txt').read_text() == expected_attempt
        and (out / 'factory-icap-deferred.txt').read_text() == expected_attempt,
        'Exactly one factory ICAP request must be archived and deferred without execution')''').body
    actual.body[index:index+1]=replacement
    reverse=copy.deepcopy(actual)
    reverse.body[index:index+len(replacement)]=[copy.deepcopy(original.body[index])]
    base.require(ast.dump(reverse,include_attributes=False)==ast.dump(original,include_attributes=False),
                 'Full derived verifier inverse AST differs')
    if pure:
        base.require(isinstance(actual.body[-2],ast.Expr) and isinstance(actual.body[-2].value,ast.Call)
                     and actual.body[-2].value.func.id=='save_new','Original isolation write boundary differs')
        actual.body=actual.body[:-3]+[ast.Return(value=ast.Name(id='result',ctx=ast.Load()))]
    actual.name='r9_factory_deferred_derived_verification'
    ast.fix_missing_locations(actual)
    exec(compile(ast.Module(body=[actual],type_ignores=[]),str(base.__file__),'exec'),base.__dict__)
    return base.r9_factory_deferred_derived_verification(out,proof)
