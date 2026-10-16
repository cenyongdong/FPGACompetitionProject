"""Independently compare configuration payloads; do not mistake headers for logic."""
from pathlib import Path
import json,hashlib,importlib.util,shutil
R=Path(__file__).resolve().parents[3];E=R/'tools/pose-v1/evidence/hdmi-board-reference-20261016-r1'
spec=importlib.util.spec_from_file_location('boot_parser',R/'tools/pose-v1/inspect_selected_boot.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
paths={
 'rebuilt_raw':E/'released-reference-products/ai7030_edif_top.bit',
 'rebuilt_Procise':E/'released-reference-products/ai7030_edif_top_disable_icap.bit',
 'selected_BOOT_rollback':E/'rollback/ai7030_top_disable_icap.bit',
 'vendor_BIT_lite':R/'Docs/26嵌赛开发/BIT/30tai_lite_detpost/ai7030_top_disable_icap.bit',
 'old_2018_factory_probe':R/'tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1/factory-bit-icap/factory-input_disable_icap.bit'}
payloads={};records={}
for name,p in paths.items():
 b=p.read_bytes();payload,header=m.bit_payload(b);payloads[name]=payload
 records[name]={'path':str(p),'file_sha256':hashlib.sha256(b).hexdigest(),'file_bytes':len(b),
                'payload_sha256':hashlib.sha256(payload).hexdigest(),'payload_bytes':len(payload),'header':header}
checks={name:payload==payloads['rebuilt_Procise'] for name,payload in payloads.items()}
base=(E/'boot-control-utf8-r2/BOOT-control.bin').read_bytes();test=(E/'boot-candidate/BOOT-reference-test.bin').read_bytes()
diff=[i for i,(a,b) in enumerate(zip(base,test)) if a!=b]
ranges=[]
for i in diff:
 if ranges and i==ranges[-1][1]:ranges[-1][1]=i+1
 else:ranges.append([i,i+1])
contexts=[]
for start,end in ranges:
 lo=start//4*4;hi=(end+3)//4*4
 def decoded(b):return b''.join(b[i:i+4][::-1] for i in range(lo,hi,4)).decode('ascii',errors='replace')
 contexts.append({'start':start,'end_exclusive':end,'old_hex':base[lo:hi].hex(),'new_hex':test[lo:hi].hex(),
                  'old_32bit_words_reversed_text':decoded(base),'new_32bit_words_reversed_text':decoded(test)})
result={'records':records,'equal_to_rebuilt_Procise_payload':checks,
 'rebuilt_Procise_equals_selected_BOOT_PL_payload':checks['selected_BOOT_rollback'],
 'BOOT_control_byte_identical_to_selected_BOOT':json.loads((E/'boot-control-utf8-r2/result.json').read_text())['byte_identical_to_selected_BOOT'],
 'candidate_BOOT_differing_bytes':len(diff),'candidate_BOOT_diff_ranges':ranges,'candidate_BOOT_difference_contexts':contexts,
 'candidate_BOOT_changed_PL_bytes':0,'candidate_BOOT_release':False,
 'correction':'Earlier semantic_scope in boot-candidate/result.json was a proposed invariant, not a passed result: its assertion failed and is preserved.',
 'conclusion':'Published reference configuration payload equals the PL payload in the selected current BOOT. Downloading it introduces no HDMI fix. No BOOT replacement/reboot is needed merely to reload this identical reference payload.',
 'actual_running_configuration_readback_verified':False,
 'limitation':'This binds files and current on-disk BOOT, not full hardware readback or absence of external JTAG changes.'}
(E/'reference-payload-review.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
shutil.copyfile(Path(__file__),E/Path(__file__).name)
print(json.dumps({'payload_equal_to_selected_BOOT':checks['selected_BOOT_rollback'],'payload_comparisons':checks,
 'candidate_BOOT_differing_bytes':len(diff),'candidate_BOOT_difference_contexts':contexts},ensure_ascii=False,indent=2))
