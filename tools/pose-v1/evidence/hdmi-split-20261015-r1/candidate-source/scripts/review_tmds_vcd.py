"""Independent read-only review of already-captured waveforms; no rerun."""
from pathlib import Path
import bisect,collections,hashlib,json
R=Path(__file__).resolve().parents[3]
E=R/'tools/pose-v1/evidence/hdmi-split-20261015-r1'
vcd=R/'tools/pose-v1/evidence/hdmi-tmds-literal-20261015-r3/simulation-copy/tmds_clock.vcd'
scope=[];wanted={};events={};header=True;time=0
names=('p7','n7','pu','nu','b7','bn7','bu','bnu')
constants={
 'tb_tmds_clock.fixed7.family_7.Inst_clk_oserdese2_10to1.txdata':'1111100000',
 'tb_tmds_clock.fixedu.ULTRASCALE_FAMILY.Inst_clk_oserdese3_10to1.txdata':'1111100000',
 'tb_tmds_clock.legacy7.family_7.Inst_clk_oserdese2_10to1.txdata':'0000110000',
 'tb_tmds_clock.legacyu.ULTRASCALE_FAMILY.Inst_clk_oserdese3_10to1.txdata':'0000110000'}
for line in vcd.read_text().splitlines():
 if header:
  a=line.split()
  if line.startswith('$scope'):scope.append(a[2])
  elif line.startswith('$upscope'):scope.pop()
  elif line.startswith('$var'):
   full='.'.join(scope+[a[4]])
   if full in constants or full in {'tb_tmds_clock.'+n for n in names}:
    wanted.setdefault(a[3],[]).append(full);events[full]=[]
  elif line.startswith('$enddefinitions'):header=False
 elif line.startswith('#'):time=int(line[1:])
 elif line and line[0] in '01xz':
  key=line[1:]
  for n in wanted.get(key,[]):events[n].append((time,line[0]))
 elif line.startswith('b'):
  value,key=line[1:].split()
  for n in wanted.get(key,[]):events[n].append((time,value.zfill(10)))
assert all(n in events for n in constants)
def value_at(n,t):
 a=events[n];i=bisect.bisect_right(a,(t,chr(127)))-1
 assert i>=0,(n,t);return a[i][1]
for n,value in constants.items():assert value_at(n,2500000)==value,(n,value_at(n,2500000))
result={}
START=2500000;END=START+128*10000
for n,neg,high in (('p7','n7',5),('pu','nu',5),('b7','bn7',2),('bu','bnu',2)):
 full='tb_tmds_clock.'+n;inv='tb_tmds_clock.'+neg
 # The bit-center observation excludes boundary propagation offsets. Check all
 # 128 characters, including bit order up to fixed phase, plus P/N complement.
 words=[]
 for k in range(128):
  word=''.join(value_at(full,START+k*10000+b*1000+500) for b in range(10))
  assert set(word)<=set('01') and word.count('1')==high,(n,k,word)
  assert sum(word[b]!=word[(b+1)%10] for b in range(10))==2,(n,k,word)
  for b in range(10):
   t=START+k*10000+b*1000+500
   assert value_at(inv,t)!=value_at(full,t),(n,k,b)
  words.append(word)
 assert len(set(words))==1,(n,collections.Counter(words))
 transitions=[(t,v) for t,v in events[full] if START<=t<END and v in '01']
 durations=collections.defaultdict(list)
 for (t,v),(nt,nv) in zip(transitions,transitions[1:]):
  if nv!=v:durations['high' if v=='1' else 'low'].append(nt-t)
 widths={k:dict(collections.Counter(a)) for k,a in durations.items()}
 if n in ('p7','b7'):
  assert set(durations['high'])=={high*1000} and set(durations['low'])=={(10-high)*1000},(n,widths)
 result[n]={'periods_checked':128,'bit_center_samples':1280,'repeated_word':words[0],
  'high_bits_per_character':high,'duty_at_bit_centers_percent':high*10,
  'edge_widths_ps':widths,'complement_checked':True,'target_Lite_branch':n in ('p7','b7')}
review={'source':str(vcd),'sha256':hashlib.sha256(vcd.read_bytes()).hexdigest(),
 'review_window_ps':[START,END],'time_unit':'1ps','kernel_reexecuted':False,
 'constant_inputs':constants,'channels':result,'independent_VCD_bitstream_review_passed':True,
 'target_7FAMILY_exact_edge_width_check_passed':True,
 'UFAMILY_exact_edge_width_test_r3_passed':False,
 'UFAMILY_observation':'Vendor behavioral/gearbox simulation shows 99ps-scale edge variation; bit-center words correct. No claim of root cause or native device behavior.',
 'r3_historical_gate_exit':1,'physical_Procise_or_silicon_signoff':False}
(E/'tmds-vcd-review.json').write_text(json.dumps(review,indent=2)+'\n')
print(json.dumps({'read_only_VCD_review_passed':True,'channels':result},ensure_ascii=False))
