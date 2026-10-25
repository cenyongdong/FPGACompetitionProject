"""Export actual consecutive HP-domain samples as VCD, CSV and static figures."""
import argparse
import csv
import json
from pathlib import Path
import shutil
import sys
import zipfile
from export_hp2_waveforms import Canvas,INK,MUTED,BORDER

R=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(R/'FPGA/hdmi_candidate/software'))
from decode_hp2_cycletrace import decode,FIELDS,FLAGS

SIGNALS=[('PS_HP2_resetn',1),('PL_HP2_resetn',1),('DDR_calibrated',1),('HP_reset',1),
         ('PS_ARVALID',1),('PS_ARREADY',1),('PS_ARADDR',32),('PS_ARID',6),
         ('PS_RVALID',1),('PS_RREADY',1),('PS_RID',6),('PS_RRESP',2),('PS_RLAST',1),('PS_RDATA',64),
         ('S01_ARVALID',1),('S01_RVALID',1),('S01_RREADY',1),('S01_RID',6),('S01_RLAST',1),('S01_RDATA',64),
         ('HC2_ARVALID',1),('HC2_RVALID',1),('HC2_RREADY',1),('HC2_RID',6),('HC2_RDATA',64)]


def vcd(path,bank):
    # Every record represents a measured rising-edge sample. No invented clock
    # or unsampled interval is inserted; time zero is the first retained sample.
    rows=bank['rows'];fields=[('HP_cycle',64)]
    fields += [(s+'_'+k,w) for s in ('PS','S01','HC2') for k,(_,w) in FIELDS.items()]
    fields += [(s+'_RDATA',64) for s in ('PS','S01','HC2')]+[(n,1) for n in FLAGS]
    fields += [('trigger_sample',1)]
    ids={n:'s'+str(i) for i,(n,w) in enumerate(fields)}
    lines=['$comment Actual BRAM samples, nominal HP 200MHz; no signal knowledge before/after window. $end',
           '$timescale 1ns $end','$scope module hp2_measured $end']
    lines += [f'$var wire {w} {ids[n]} {n} $end' for n,w in fields]
    lines += ['$upscope $end','$enddefinitions $end']
    for i,row in enumerate(rows):
        lines.append('#'+str(i*5))
        for name,width in fields:
            value=int(i==bank['trigger_index']) if name=='trigger_sample' else row[name]
            lines.append((str(value) if width==1 else 'b'+format(value,f'0{width}b')+' ')+ids[name])
    lines.append('#'+str(len(rows)*5))
    lines += [('x' if w==1 else 'bx ')+ids[n] for n,w in fields]
    path.write_text('\n'.join(lines)+'\n')


def figure(base,bank):
    rows=bank['rows'];n=len(rows);idx=bank['trigger_index']
    c=Canvas(1980,260+len(SIGNALS)*48)
    title='首次 PS RVALID' if bank['bank']==0 else 'PL 互联 resetn 首次为高'
    c.text(38,25,'HP2 实板连续采样 / '+title,32,bold=True)
    edge='窗口初始已高，不能认定为释放边沿' if bank['trigger_initial_high'] else '触发点前后均有实测样本'
    c.text(38,80,f'名义 200 MHz · 每点 5 ns · {n} 点 · HP周期 {rows[0]["HP_cycle"]}–{rows[-1]["HP_cycle"]} · {edge}',22,MUTED)
    c.text(38,118,'板内 BRAM 实测；横轴：相对触发时间（ns）；总线值：十六进制。数据/ID/响应仅在 RVALID=1 时有效。',21,MUTED)
    left,right,top=300,1930,185
    xx=lambda i:left+(right-left)*i/n
    for tick in range(0,n+1,8):
        c.line([(xx(tick),top-12),(xx(tick),top+len(SIGNALS)*48)],BORDER,1)
        c.text(xx(tick)-15,top+len(SIGNALS)*48+12,str((tick-idx)*5),18,MUTED)
    c.line([(xx(idx),top-15),(xx(idx),top+len(SIGNALS)*48)],'#ca3647',2,True)
    for j,(name,width) in enumerate(SIGNALS):
        y=top+j*48;color='#c83a45' if name.startswith('PS_R') else ('#d57d20' if name.startswith('S01') else '#2676af')
        c.text(38,y,'PL_DDR_calibrated' if name=='DDR_calibrated' else name,21,INK,bold=name.endswith('RVALID'))
        if width==1:
            points=[]
            for i,row in enumerate(rows):
                yy=y+(5 if row[name] else 30)
                if points:points.append((xx(i),points[-1][1]))
                points.extend([(xx(i),yy),(xx(i+1),yy)])
            c.line(points,color,3)
        else:
            start=0
            for end in range(1,n+1):
                if end<n and rows[end][name]==rows[start][name]:continue
                a,b=xx(start),xx(end)
                c.line([(a+2,y+5),(b-2,y+5),(b,y+18),(b-2,y+31),(a+2,y+31),(a,y+18),(a+2,y+5)],color,1)
                text=format(rows[start][name],f'0{(width+3)//4}X')
                if b-a>len(text)*13+8:c.text(a+8,y+8,text,18,color)
                start=end
    c.text(38,c.h-35,'单点为源时钟上升沿观测；异步复位/状态引脚存在采样边沿不确定性；窗口之外无连续信号证据。',20,MUTED)
    c.save(base)


def main():
    p=argparse.ArgumentParser();p.add_argument('raw',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    snapshot=json.loads(a.raw.read_text());d=decode(snapshot)
    a.output.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(a.raw,a.output/'raw.json')
    (a.output/'decoded.json').write_text(json.dumps(d,indent=2)+'\n')
    summaries=[]
    for bank in d['banks']:
        if not bank['published']:
            summaries.append(f'Bank {bank["bank"]}: 未触发／未发布，不生成虚构波形。');continue
        base=a.output/('bank'+str(bank['bank']))
        vcd(base.with_suffix('.vcd'),bank);figure(base,bank)
        columns=['sample_index','relative_trigger_ns',*bank['rows'][0].keys()]
        with base.with_suffix('.csv').open('w',newline='',encoding='utf-8-sig') as f:
            writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader()
            for i,row in enumerate(bank['rows']):
                values={k:('0x'+format(v,'016X' if k.endswith('RDATA') else '08X')
                           if k.endswith(('RDATA','ARADDR')) else v) for k,v in row.items()}
                writer.writerow(dict(sample_index=i,relative_trigger_ns=5*(i-bank['trigger_index']),**values))
        summaries.append(f'Bank {bank["bank"]}: {bank["count"]} 点，触发 HP 周期 {bank["trigger_cycle"]}，握手 {bank["handshakes"]}。')
    (a.output/'README.md').write_text('# HP2 实板连续波形\n\n'+ '\n\n'.join(summaries)+
        '\n\n采样器在 FPGA 配置后自主工作，512 bit × 128 点 × 2 窗口，每点名义 5 ns。'+
        '保留触发前最多32点与触发后95点；PS出口、互联S01、AI HC2在同一HP域取样。'+
        'AI／S01连接状态以本次实验配置为准；原始信号包含PS、S01与HC2观察点。软件只读冻结缓冲，未加载SDK、未发DMA或HDMI START。\n\n'+
        'PNG/SVG供直接查看，VCD供波形工具逐拍检查，CSV包含全部样本，RDATA/ARADDR以十六进制保存以避免表格软件截断64位精度。VCD时间0对应各窗口首样本；末端置X表示超出观测范围。'+
        'raw.json为原始32位CSR读值，decoded.json为按RTL布局解码的结果。\n\n'+
        '\n'.join('- '+s for s in d['limits'])+'\n',encoding='utf-8')
    for name in ('decode_hp2_cycletrace.py','capture_hp2_cycletrace.py'):
        shutil.copyfile(R/'FPGA/hdmi_candidate/software'/name,a.output/name)
    shutil.copyfile(R/'FPGA/hdmi_candidate/diagnostics/hp2_cycle_trace.sv',a.output/'hp2_cycle_trace.sv')
    print(json.dumps({'output':str(a.output),'banks':summaries},ensure_ascii=False))


if __name__=='__main__':main()
