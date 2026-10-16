"""Independently resolve the two generated comment-only identity differences."""
import jfm_build_support as s
import json,re,difflib,hashlib
src=s.R/'Docs/26嵌赛开发/fpai_demo_fpga';ref=s.W/'reference'
old=json.loads((s.E/'generated-contract-review.json').read_text(encoding='utf-8'))
assert not old['XCI_with_differences']
names=old['original_RTL_DDR_PRJ_EDIF_XDC_changes']
assert set(names)=={'rtl/ip/mig_7series_0/mig_7series_0/example_design/par/example_top.xdc','fpai_demo_vivado.srcs/sources_1/bd/ps_ai/hdl/ps_ai_wrapper.v'}
reports=[]
for n in names:
 a=(src/n).read_text();b=(ref/n).read_text()
 pattern=r'^//(?:Date        |Host        ):[^\n]*\n' if n.endswith('.v') else r'^##  (?:Mon|Tue|Wed|Thu|Fri|Sat|Sun) [^\n]*\n'
 assert re.sub(pattern,'',a,flags=re.M)==re.sub(pattern,'',b,flags=re.M),n
 reports.append({'path':n,'original_SHA':hashlib.sha256((src/n).read_bytes()).hexdigest(),
 'generated_SHA':hashlib.sha256((ref/n).read_bytes()).hexdigest(),'difference':'generated timestamp/host comments only',
 'full_diff':''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='original',tofile='generated'))})
s.dump(s.E/'generated-contract-reviewed.json',{'initial_strict_byte_assertion_preserved':'generated-contract-review.json',
 'XCI_parameter_differences':0,'functional_RTL_DDR_PRJ_EDIF_XDC_differences':0,'comment_only_files':reports,
 'gate_pass':True,'source_or_generated_files_modified_to_pass':False})
print('Original XCI parameters and functional source contracts PASS; two generated metadata-only differences retained')
