"""Export full raw protocol-error windows, preserving 64/160-bit precision."""
import argparse,csv,json,shutil,sys
from pathlib import Path
from export_hp2_waveforms import Canvas,INK,MUTED
R=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(R/'FPGA/hdmi_candidate/software'))
from decode_hp2_protocol import decode,FIELDS,WRITE_FIELDS,PROTOCOL_FLAGS

SIGNALS=[('PS_HP2_resetn',1),('PL_HP2_resetn',1),('HP_reset',1),
 ('PC_system_resetn',1),('PC_checker_ready',1),('PC_seen_reset_low',1),('PC_status',160),
 ('PS_ARVALID',1),('PS_ARREADY',1),('PS_ARADDR',32),('PS_ARID',6),('PS_ARLEN',4),
 ('PS_RVALID',1),('PS_RREADY',1),('PS_RID',6),('PS_RLAST',1),('PS_RRESP',2),('PS_RDATA',64),
 ('PS_AWVALID',1),('PS_AWREADY',1),('PS_AWADDR',32),('PS_AWID',6),('PS_AWLEN',4),
 ('PS_WVALID',1),('PS_WREADY',1),('PS_WID',6),('PS_WLAST',1),('PS_WDATA',64),
 ('PS_BVALID',1),('PS_BREADY',1),('PS_BID',6),('PS_BRESP',2)]

def export_files(folder,result):
 rows=result['rows'];fields=[('HP_cycle',64)]
 fields += [('PS_'+name,width) for name,(_,width) in FIELDS.items()]
 fields += [('PS_RDATA',64)]+[('PS_'+name,width) for name,(_,width) in WRITE_FIELDS.items()]
 fields += [(name,1) for name in PROTOCOL_FLAGS]+[('raw_flags',32),('PC_status',160)]
 # The write bundle and raw flags share three VALID names; declare each signal once.
 fields=list(dict(fields).items())
 ids={name:'s'+str(i) for i,(name,_) in enumerate(fields)}
 lines=['$comment Source boot_id='+result['boot_id']+'; monitor_input_register_cycles='+str(result.get('monitor_input_register_cycles',0))+'; consecutive samples, no coverage outside this window. $end',
  '$timescale 1ns $end','$scope module hp2_protocol $end']
 lines += [f'$var wire {width} {ids[name]} {name} $end' for name,width in fields]
 lines += ['$var wire 1 trigger trigger_sample $end','$upscope $end','$enddefinitions $end']
 for i,row in enumerate(rows):
  lines.append('#'+str(i*5))
  lines += [(str(row[name]) if width==1 else 'b'+format(row[name],f'0{width}b')+' ')+ids[name] for name,width in fields]
  lines.append(str(int(i==result['trigger_index']))+'trigger')
 lines += ['#'+str(5*len(rows))]+[('x' if width==1 else 'bx ')+ids[name] for name,width in fields]+['xtrigger']
 (folder/'protocol.vcd').write_text('\n'.join(lines)+'\n')
 hexadecimal={'PS_RDATA':16,'PS_WDATA':16,'PS_ARADDR':8,'PS_AWADDR':8,'PC_status':40}
 with (folder/'protocol.csv').open('w',newline='',encoding='utf-8') as stream:
  writer=csv.DictWriter(stream,fieldnames=['relative_ns']+[name for name,_ in fields]);writer.writeheader()
  for i,row in enumerate(rows):
   writer.writerow(dict(relative_ns=(i-result['trigger_index'])*5,
    **{name:('0x'+format(row[name],f'0{hexadecimal[name]}x') if name in hexadecimal else row[name]) for name,_ in fields}))

def figure(folder,result,input_register_cycles=0):
 rows=result['rows'];n=len(rows);step=47;height=210+step*len(SIGNALS)+85
 c=Canvas(2200,height);simulation=result['boot_id'].startswith('SIMULATION')
 title='HP2 首次非建议指示窗口' if result.get('trigger_semantics') else 'HP2 首次原生协议检查指示'
 c.text(38,25,('仿真验证 / ' if simulation else '实板连续采样 / ')+title,32,bold=True)
 c.text(38,80,f'HP周期 {rows[0]["HP_cycle"]}–{rows[-1]["HP_cycle"]} · 每点名义5ns · '+('仿真数据，不是实板波形' if simulation else '板内BRAM原始采样'),22,MUTED)
 c.text(38,118,'横轴相对首次检查指示触发时间（ns）；总线值为十六进制。数据/ID/响应/末拍仅在所属VALID=1时有效。',21,MUTED)
 left,right,top=330,2150,185;xx=lambda i:left+(right-left)*i/n
 for tick in range(0,n+1,8):
  x=xx(tick);c.line([(x,top-12),(x,top+step*len(SIGNALS))], '#dce5ef',1)
  c.text(x-13,top+step*len(SIGNALS)+15,str((tick-result['trigger_index'])*5),18,MUTED)
 tx=xx(result['trigger_index']);c.line([(tx,top-12),(tx,top+step*len(SIGNALS))],'#e2465e',2)
 for k,(name,width) in enumerate(SIGNALS):
  y=top+k*step;colour='#da3048' if name.startswith('PC_') else '#2678b7'
  if name.startswith('PS_R'):colour='#da3048'
  if name.startswith('PS_W') or name.startswith('PS_B') or name.startswith('PS_AW'):colour='#a56215'
  c.text(38,y-4,name,21,INK,bold=name.endswith('VALID') or name=='PC_status')
  if width==1:
   points=[]
   for i,row in enumerate(rows):
    v=y+(0 if row[name] else 22)
    if i:points.append((xx(i),y+(0 if rows[i-1][name] else 22)))
    points.append((xx(i),v))
   points.append((xx(n),y+(0 if rows[-1][name] else 22)))
   c.line(points,colour,2)
  else:
   start=0
   while start<n:
    end=start+1
    while end<n and rows[end][name]==rows[start][name]:end+=1
    a,b=xx(start),xx(end);c.line([(a,y),(b,y)],colour,1);c.line([(a,y+23),(b,y+23)],colour,1)
    c.line([(a,y),(a+2,y+11),(a,y+23)],colour,1)
    value=format(rows[start][name],f'0{(width+3)//4}x')
    if b-a>max(35,len(value)*10):c.text(a+6,y+1,value,17,colour)
    start=end
 c.text(38,height-38,f'监测输入寄存{input_register_cycles}个HP周期；pc_status另含原生IP流水延迟。窗口之外不代表已知信号。',19,MUTED)
 c.save(folder/'protocol')

def main():
 p=argparse.ArgumentParser();p.add_argument('raw',type=Path);p.add_argument('output',type=Path);p.add_argument('--input-register-cycles',type=int,choices=(0,1),default=0);a=p.parse_args()
 result=decode(json.loads(a.raw.read_text()));result['monitor_input_register_cycles']=a.input_register_cycles;a.output.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(a.raw,a.output/'protocol-raw.json')
 (a.output/'protocol-decoded.json').write_text(json.dumps(result,indent=2)+'\n')
 if result['published']:export_files(a.output,result);figure(a.output,result,a.input_register_cycles)
 print(json.dumps({'published':result['published'],'fired':result['fired'],'output':str(a.output)}))

if __name__=='__main__':main()
