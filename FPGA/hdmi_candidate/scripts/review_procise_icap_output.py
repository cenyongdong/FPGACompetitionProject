"""Inspect output structure and actual packet/byte differences; no patch retry."""
import jfm_build_support as s
from pathlib import Path
import json,struct,hashlib
root=s.W/'factory-bit-icap';a=(root/'factory-input.bit').read_bytes();b=(root/'factory-input_disable_icap.bit').read_bytes()
def header(data):
 pos=0
 def short():
  nonlocal pos
  n=struct.unpack_from('>H',data,pos)[0];pos+=2;return n
 n=short();pos+=n;assert short()==1
 d={}
 for key in b'abcd':
  assert data[pos]==key;pos+=1;n=short();d[chr(key)]=data[pos:pos+n].rstrip(b'\0').decode('ascii');pos+=n
 assert data[pos]==ord('e');pos+=1;n=struct.unpack_from('>I',data,pos)[0];pos+=4
 assert pos+n==len(data)
 return d,pos,data[pos:]
ah,ap,aa=header(a);bh,bp,bb=header(b)
prefix=0
while prefix<min(len(aa),len(bb)) and aa[prefix]==bb[prefix]:prefix+=1
suffix=0
while suffix<min(len(aa),len(bb))-prefix and aa[-suffix-1]==bb[-suffix-1]:suffix+=1
result={'input_header':ah,'output_header':bh,'input_payload_bytes':len(aa),'output_payload_bytes':len(bb),
 'input_payload_offset':ap,'output_payload_offset':bp,'common_payload_prefix_bytes':prefix,'common_payload_suffix_bytes':suffix,
 'same_offset_changed_payload_bytes':sum(x!=y for x,y in zip(aa,bb)),
 'tool_exit_zero_and_output_created':True,'warnings':['Missing Bit Patch Info','Missing Patch Version Info','VCCM Absent, Bitstream Patch Inactive'],
 'ICAP_silicon_semantics_independently_proven':False,'BOOT_or_hardware_acceptance':False,
 'note':'Command success and structural output are actual; do not interpret VCCM inactivity as ICAP result without separate evidence'}
s.dump(s.E/'factory-bit-icap/structural-review.json',result)
print(json.dumps(result,ensure_ascii=True))
