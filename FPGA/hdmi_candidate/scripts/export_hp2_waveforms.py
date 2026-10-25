"""Export measured GP event reconstructions and exact raw logs; no board access.

Requires Pillow. SVG and PNG share the same drawing coordinates. VCD contains
recorded synchronized level changes only, with no invented clocks or R beats.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import html
import importlib.util
import json
import shutil
import tarfile
import zipfile
from PIL import Image,ImageDraw,ImageFont

R=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('release_decode',R/'FPGA/hdmi_candidate/software/decode_ps_release.py')
decoder=importlib.util.module_from_spec(spec);spec.loader.exec_module(decoder)
CASES={'r26':'hdmi-ps-release-20261020-r26','r28':'hdmi-s01-isolation-20261022-r28','r29':'hdmi-s01-soak-20261022-r29'}
SIGNALS=[('PS_HP2_resetn','PS HP2 resetn'),('PL_HP2_resetn','PL HP2 resetn'),
         ('DDR_calibrated','DDR calibrated'),('PS_ARVALID','PS ARVALID'),
         ('PS_RVALID','PS RVALID'),('HDMI_ARVALID','S01 ARVALID'),('HDMI_RVALID','S01 RVALID')]
COLORS={'PS_RVALID':'#cf3545','HDMI_RVALID':'#df7b15','PL_HP2_resetn':'#237ac1',
        'DDR_calibrated':'#188766','PS_HP2_resetn':'#475569','PS_ARVALID':'#566478','HDMI_ARVALID':'#566478'}
BG='#f6f8fc';INK='#17263c';MUTED='#52637a';BORDER='#dbe3ed'


def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def write_csv(path,columns,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=columns);w.writeheader();w.writerows(rows)


class Canvas:
    def __init__(self,width,height):
        self.w,self.h=width,height
        self.image=Image.new('RGB',(width,height),BG);self.d=ImageDraw.Draw(self.image)
        self.svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
        self.fonts={}
        self.rect(0,0,width,height,BG)
    def rect(self,x,y,w,h,fill='white',stroke=None):
        self.d.rectangle((x,y,x+w,y+h),fill=fill,outline=stroke,width=1)
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke or "none"}"/>')
    def text(self,x,y,s,size=27,color=INK,bold=False):
        key=(size,bold)
        if key not in self.fonts:
            self.fonts[key]=ImageFont.truetype('C:/Windows/Fonts/'+('msyhbd.ttc' if bold else 'msyh.ttc'),size)
        self.d.text((x,y),s,font=self.fonts[key],fill=color,anchor='lt')
        self.svg.append(f'<text x="{x}" y="{y}" dominant-baseline="text-before-edge" fill="{color}" '
                        f'font-family="Microsoft YaHei, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}">{html.escape(str(s))}</text>')
    def line(self,points,color=BORDER,width=2,dashed=False):
        self.d.line(points,fill=color,width=width)
        self.svg.append(f'<polyline points="{" ".join(f"{x},{y}" for x,y in points)}" fill="none" stroke="{color}" stroke-width="{width}" '
                        +(f'stroke-dasharray="7 5" ' if dashed else '')+'/>' )
    def dot(self,x,y,color):
        self.d.ellipse((x-5,y-5,x+5,y+5),fill=color)
        self.svg.append(f'<circle cx="{x}" cy="{y}" r="5" fill="{color}"/>')
    def save(self,base):
        self.image.save(base.with_suffix('.png'))
        base.with_suffix('.svg').write_text('\n'.join(self.svg+['</svg>']),encoding='utf-8')


def state(case,cycle):
    found=None
    for e in case['d']['events']:
        if e['GP_cycle']>cycle:break
        found=e['levels']
    return found


def waves(c,case,x,y,width,start,end,ticks,origin=0,row=59):
    left=x+310;right=x+width-30
    xx=lambda cycle:left+(cycle-start)/(end-start)*(right-left)
    bottom=y+len(SIGNALS)*row
    c.rect(x,y-16,width,bottom-y+82,'white',BORDER)
    first=case['d']['events'][0]['GP_cycle']
    if start<first:
        c.rect(left,y-10,max(0,xx(min(first,end))-left),bottom-y+18,'#e9edf3')
    for tick in ticks:
        v=tick+origin
        if start<=v<=end:
            c.line([(xx(v),y-6),(xx(v),bottom+3)],BORDER,1)
            c.text(xx(v)-14,bottom+16,str(tick),20,MUTED)
    for i,(name,label) in enumerate(SIGNALS):
        top=y+i*row;lo=top+35;hi=top+9
        c.text(x+20,top+12,label,23,INK,name in ('PS_RVALID','HDMI_RVALID'))
        c.line([(left,lo),(right,lo)],'#edf1f6',1)
        points=[];known=state(case,start)
        if known is not None:points=[(left,hi if known[name] else lo)]
        previous=known[name] if known else None
        for e in case['d']['events']:
            t=e['GP_cycle']
            if not start<t<=end:continue
            value=e['levels'][name]
            if previous is None:points=[(xx(t),hi if value else lo)];c.dot(xx(t),points[-1][1],COLORS[name])
            elif value!=previous:
                points.extend([(xx(t),hi if previous else lo),(xx(t),hi if value else lo)])
                c.dot(xx(t),hi if value else lo,COLORS[name])
            previous=value
        if points:
            points.append((right,hi if previous else lo));c.line(points,COLORS[name],4)
        c.text(right+5,hi-3,'1',15,MUTED);c.text(right+5,lo-3,'0',15,MUTED)
    return bottom+80


def header(c,title,subtitle):
    c.text(65,38,title,45,bold=True)
    c.text(65,103,subtitle,27,MUTED)
    c.text(65,152,'硬件事件记录重绘；非 ILA 逐周期连续波形。仅反映 GP 域同步后电平，可能漏掉短脉冲。',25,'#945612')


def cards(c,y,items):
    width=(c.w-160-35*(len(items)-1))/len(items)
    for i,(title,lines) in enumerate(items):
        x=80+i*(width+35);c.rect(x,y,width,65+len(lines)*44,'white',BORDER)
        c.text(x+22,y+18,title,28,bold=True)
        for j,line in enumerate(lines):c.text(x+22,y+68+44*j,line,24,MUTED)


def figures(cases,out):
    a,b,z=cases['r26'],cases['r28'],cases['r29']
    release=z['release'];d=z['d'];w=z['words']
    c=Canvas(2500,1740)
    header(c,'01  隔离版故障：启动阶段已出现 PS HP2 返回',
           'r29｜同一隔离 BOOT：f4bed59ec077…｜AI 四路保持｜SDK / DMA / HDMI START = 0')
    c.text(80,218,'A. 最早可观测状态（GP 本域周期）',30,bold=True)
    waves(c,z,80,283,2340,0,60,[0,3,20,39,60])
    c.text(420,806,'灰区：首条记录之前未知；GP=3 时 PS RVALID 已为 1，不能据此推断更早的请求历史。',25,MUTED)
    c.text(80,862,f'B. PL 释放附近放大（横轴为 GP 周期 − {release:,}；每周期名义 10 ns）',30,bold=True)
    waves(c,z,80,930,2340,release-40,release+12,[-40,-24,-10,0,3,12],release)
    cards(c,1455,[('HP 域首事件（独立计时）',[
        f'首个 PS RVALID：{d["first_raw_PS_RVALID_HP_cycle"]:,}',
        f'PL 就绪时首 R：{d["first_PL_ready_PS_RVALID_HP_cycle"]:,}',
        '不能与 GP 周期直接对齐']),('HP 原始累计 / 返回属性',[
        'PS AR 握手 = 0；PS R 原始握手 = 6',
        'RID = 32；RRESP = OKAY；RLAST = 0',
        'R=6 不代表 6 笔合法事务']),('冻结短窗（六边界）',[
        f'{w[1]:,} HP 周期 ≈ {w[1]/200:.3f} μs',
        'PS / S01：RVALID=1、RREADY=0',
        'S01 源输入为 0；30 分钟未完成'])])
    c.text(80,1698,'边界：配置前 / 无观测时钟阶段不可见；初始 resetn=1 不是已捕获的释放边沿。',22,MUTED)
    c.save(out/'01_r29_isolated_fault')

    c=Canvas(2500,1290)
    header(c,'02  完全相同隔离镜像：一次健康，一次故障',
           'r28 与 r29 使用相同 bit / BOOT；两次之间没有重新实现，AI 四路连接保持')
    for x,case,title in [(70,b,'r28：健康启动样本'),(1280,z,'r29：故障启动样本')]:
        c.text(x+10,228,title,33,bold=True,color='#188766' if case is b else '#cf3545')
        waves(c,case,x,300,1150,case['release']-36,case['release']+12,[-30,-20,-10,0,3,10],case['release'])
        d=case['d'];c.text(x+20,848,f'绝对 PL 释放周期：{case["release"]:,}',26,MUTED)
        c.text(x+20,895,f'HP 累计 PS AR / R = {d["raw_HP_handshakes"]["PS_AR"]} / {d["raw_HP_handshakes"]["PS_R"]}',27,INK)
        c.text(x+20,942,'PS 首个 RVALID：'+('未记录到' if d['first_raw_PS_RVALID_HP_cycle'] is None else f'HP {d["first_raw_PS_RVALID_HP_cycle"]:,}'),26,MUTED)
    c.text(80,1040,'横轴均以各自 PL 释放为 0，仅用于形态对照；不是跨启动时钟同步。',27,MUTED)
    c.text(80,1100,'实测结论：仅隔离 HDMI / 旧视频源端不足以消除该故障。',34,'#bf3544',True)
    c.text(80,1162,'保留的 S01 互联内部、PS 初始化 / 复位覆盖及配置前事务仍未排除。',27,MUTED)
    c.text(80,1225,'两次均无 SDK / 推理 / START；首条 GP 记录之前未知，GP 同步日志可能漏掉短脉冲。',23,MUTED)
    c.save(out/'02_same_image_healthy_vs_fault')

    c=Canvas(2500,1370)
    header(c,'03  视频连接与源端隔离：两种故障样本的返回形态',
           'r26：原共享连接｜r29：仅源端隔离、互联 S01 内部仍保留｜两者均保持 AI 四路')
    for x,case,title in [(70,a,'r26：视频仍连接'),(1280,z,'r29：视频源端已隔离')]:
        c.text(x+10,228,title,33,bold=True)
        waves(c,case,x,300,1150,case['release']-30,case['release']+10,[-24,-10,0,5,10],case['release'])
        d=case['d'];pins=d['first_raw_PS_RVALID_pins']
        c.text(x+20,848,f'HP 累计 PS AR / R = {d["raw_HP_handshakes"]["PS_AR"]} / {d["raw_HP_handshakes"]["PS_R"]}',28,INK)
        c.text(x+20,899,f'首 R：RID={pins&63}，RRESP={(pins>>6)&3}，RLAST={(pins>>8)&1}',26,MUTED)
        lines=['PL 释放后 +2 GP：PS RVALID 降低','+3 GP：S01 / HDMI RVALID 升高'] if case is a else ['PS RVALID 未记录到下降','PL 释放后 +3 GP：S01 RVALID 升高']
        for j,s in enumerate(lines):c.text(x+20,950+j*44,s,25,MUTED)
    c.text(80,1098,'横轴：各自 PL 释放前后 GP 周期（名义 10 ns / 周期）。',26,MUTED)
    c.text(80,1153,'同步后先后形态不能当作源域精确传播延迟；HP 累计 R 是原始管脚握手。',27,'#945612')
    c.text(80,1210,'r26 的 S01 返回连接功能 HDMI reader；r29 的 S01 返回仅被观测，reader 已断开。',27,MUTED)
    c.text(80,1270,'未出现已观测 AR 不等于证明配置前没有请求；本图不构成 PS 内部 FIFO 状态证据。',24,MUTED)
    c.save(out/'03_connected_vs_isolated_fault')


def vcd(path,case,start,end,zoom):
    names=[n.replace('HDMI_','S01_') for n in decoder.LEVELS]
    ids=[chr(33+i) for i in range(len(names))];cycle_id='G';valid_id='V'
    lines=['$date 2026-10-22 $end','$version Hardware event-log reconstruction; NOT ILA continuous capture $end',
           '$timescale 10ns $end',f'$comment Original GP origin={start}; nominal GP100MHz; GP and HP clocks are independent. $end',
           '$comment No clocks, R beats, RDATA or unrecorded pulses have been synthesized. $end',
           '$scope module gp_sync_observations $end']
    lines += [f'$var wire 1 {i} {n} $end' for i,n in zip(ids,names)]
    lines += [f'$var wire 64 {cycle_id} original_GP_cycle $end',f'$var wire 1 {valid_id} observation_valid $end',
              '$upscope $end','$enddefinitions $end','#0']
    initial=state(case,start) if zoom else None
    lines += [(str(int(initial[n])) if initial else 'x')+i for i,n in zip(ids,decoder.LEVELS)]
    lines += [f'b{start:b} {cycle_id}',('1' if initial else '0')+valid_id]
    for e in case['d']['events']:
        t=e['GP_cycle']
        if not start<t<=end:continue
        lines += [f'#{t-start}',f'b{t:b} {cycle_id}','1'+valid_id]
        lines += [str(int(e['levels'][n]))+i for i,n in zip(ids,decoder.LEVELS)]
    lines += [f'#{end-start}',f'b{end:b} {cycle_id}',f'#{end-start+1}','0'+valid_id]
    lines += ['x'+i for i in ids]
    path.write_text('\n'.join(lines)+'\n',encoding='ascii')


def load_case(assets,out,key,directory):
    root=assets/'tools/pose-v1/evidence'/directory
    with tarfile.open(root/'board-evidence.tar.gz') as t:
        members={'startup_snapshot.jsonl':'run-1/release/raw.jsonl','axi_snapshot.jsonl':'run-1/legacy/trace.jsonl',
                 'probe.stderr.log':'run-1/legacy/stderr.log','probe.stdout.log':'run-1/legacy/stdout.log'}
        raw=out/'raw'/key;raw.mkdir(parents=True)
        for name,member in members.items():(raw/name).write_bytes(t.extractfile(member).read())
    records=[json.loads(x) for x in (raw/'startup_snapshot.jsonl').read_text().splitlines()]
    row=next(x for x in records if x.get('event')=='ps_release_snapshot')
    d=decoder.decode(row['words'])
    if d['event_overflow'] or d['HP_count_overflow_mask']:
        raise RuntimeError('Cannot draw complete held state through overflowed evidence: '+key)
    rows=[json.loads(x) for x in (raw/'axi_snapshot.jsonl').read_text().splitlines()]
    words=rows[0]['words']
    if len(words)!=104 or words[0]!=0x41495201:raise RuntimeError('Wrong raw AXI identity')
    case=dict(key=key,d=d,words=words,release=d['first_GP_cycle']['PL_release_or_initial_high'])
    summary=json.loads((root/'board-summary.json').read_text())
    package=json.loads((assets/'tools/pose-v1/evidence'/CASES['r28']/'package-review.json').read_text()) if key=='r29' else json.loads((root/'package-review.json').read_text())
    case['meta']=dict(case=key,source_package=directory,BOOT_sha256=package['sha256'],
        source_isolated=key!='r26',candidate_boot_id=summary.get('candidate_boot_id'),
        GP_clock_nominal_Hz=100000000,HP_clock_nominal_Hz=200000000,SDK=0,inference=0,HDMI_START=0,
        GP_event_overflow=False,HP_count_overflow_mask=0,
        S01_current_pins=hex(words[83]),S01_source_input_mask=hex(words[83]&0x7fff9),
        short_window_HP_cycles=words[1],GP_freeze_cycle=d['GP_freeze_cycle'],HP_freeze_cycle=d['HP_freeze_cycle'])
    dump(out/'decoded'/(key+'_startup.json'),d);dump(raw/'case.json',case['meta'])
    event_rows=[dict(GP_cycle=e['GP_cycle'],GP_cycle_relative_PL=e['GP_cycle']-case['release'],
                     nominal_time_ns=e['GP_cycle']*10,**{n:int(v) for n,v in e['levels'].items()}) for e in d['events']]
    write_csv(out/'tables'/(key+'_GP_events.csv'),list(event_rows[0]),event_rows)
    hp=[]
    for label,field,pin_field in [('first_raw_PS_RVALID','first_raw_PS_RVALID_HP_cycle','first_raw_PS_RVALID_pins'),
                                 ('first_PL_ready_PS_RVALID','first_PL_ready_PS_RVALID_HP_cycle','first_PL_ready_PS_RVALID_pins')]:
        pins=d[pin_field];hp.append(dict(record=label,HP_cycle=d[field],raw_pins_hex='' if pins is None else hex(pins),
            RID='' if pins is None else pins&63,RRESP='' if pins is None else (pins>>6)&3,RLAST='' if pins is None else (pins>>8)&1))
    write_csv(out/'tables'/(key+'_HP_first_events.csv'),list(hp[0]),hp)
    global_names=['ABI','HP_cycles_mod32','source_flags','reset_cycles_mod32','reserved4','reserved5','reserved6','reserved7']
    fields=['AR_handshakes','R_handshakes','RLAST_handshakes','RRESP_nonOKAY','AR_backpressure_cycles','R_backpressure_cycles',
            'ARVALID_cycles','RVALID_cycles','last_ARADDR','last_AR_meta','last_R_meta','current_pins','first_error_meta','first_error_cycle','last_event_cycle','expected_R_beats_mod32']
    word_rows=[dict(word=i,meaning=global_names[i] if i<8 else f'channel{(i-8)//16}.'+fields[(i-8)%16],decimal=value,hex=hex(value)) for i,value in enumerate(words)]
    write_csv(out/'tables'/(key+'_AXI_104_words.csv'),list(word_rows[0]),word_rows)
    (out/'vcd').mkdir(exist_ok=True)
    vcd(out/'vcd'/(key+'_GP_full.vcd'),case,0,d['GP_freeze_cycle'],False)
    vcd(out/'vcd'/(key+'_GP_release_zoom.vcd'),case,case['release']-40,case['release']+15,True)
    return case


def finish_export(out,archive):
    notes='''# HDMI / PS HP2 实测波形与原始记录

整理日期：2026-10-22。用于厂商技术答疑；本包完全来自已保存实板记录，没有新增启动或板端访问。

## 先看什么

- `01_r29_isolated_fault.png`：最新隔离故障，最早观察状态与PL释放附近放大，附HP原始首事件及短窗计数。
- `02_same_image_healthy_vs_fault.png`：完全相同隔离bit／BOOT的健康与故障启动对照。
- `03_connected_vs_isolated_fault.png`：视频保持连接与源端隔离时的两个故障样本。
- 同名SVG可缩放；PNG已检查中文和版面，适合直接发群。

## 数据是什么，不能解释成什么

这些图是FPGA内被动事件记录器的实测数据重绘，**不是ILA逐周期连续抓波，也不是RTL仿真波形**。

GP记录器以名义100MHz采集经同步后的电平变化，保存每条变化的64位GP周期。三例事件表均未溢出。
图中阶梯线表示日志中同步电平的保持关系；不能据此排除比同步采样更短的原始脉冲。实心点表示首条记录或该信号的记录变化。
记录前未知区域在图中标灰；初态resetn=1不证明捕获到了释放边沿。

HP记录器以名义200MHz直接记录原始握手累计和首RVALID事件。HP与GP计数起点、停钟和FREEZE切面不同，**不能把两个域的周期数直接对齐**。
图中的纳秒／微秒只按既有时钟约束折算，不是示波器测得的周期。未捕获配置前及无观测时钟阶段。

没有保存逐拍RDATA、六次R握手的各自时间戳或原生ILA的WDB／LTX文件。HP累计R=6是六次原始管脚握手，不证明六笔合法事务。
RVALID=1且RREADY=0本身符合背压保持规则；疑点是请求来源和初始化／复位经历。
本包不能直接证明PS内部FIFO占用、FIFO残留或DDR颗粒硬件故障。

## 三个样本

| 标识 | 视频连接 | 结果 | SDK／推理／HDMI START |
|---|---|---|---|
| r26 | 原双输入HP2共享结构，功能视频分支仍连接 | 故障，PS AR=0、原始R=1 | 全部0 |
| r28 | S01全部27个主机输入置0，双输入互联内部保留 | 单次健康，PS AR=0、原始R=0 | 全部0 |
| r29 | 与r28完全相同隔离bit／BOOT | 再次启动故障，PS AR=0、原始R=6 | 全部0 |

AI四路均保持HC0→HP0、HC1→HP1、HC2→HP2互联S00、HC3→HP3。
r28／r29的BOOT SHA256均为`f4bed59ec07751bcd7eaac332d9524675e071a4eff1226a4f9b5bdd1642bde04`。
隔离版只断开视频源端，保留S01互联内部；图中S01返回并不是已断开的功能HDMI reader输入。
r29计划30分钟无SDK驻留，但启动记录已锁存故障，首次检查即提前冻结取证；**30分钟未完成，不能报告长期通过**。
每例均已完成原BOOT回退，本次导出没有写BOOT、重启或SDK操作。

## 文件及复核

- `raw/r*/startup_snapshot.jsonl`：原始128字PS／PL记录及19字启动见证，从既有板端归档逐字节提取。
- `raw/r*/axi_snapshot.jsonl`：原始104字六边界快照；r29另含驻留提前停止的原始时长／标志记录。
- `raw/r*/probe.stdout.log`与`probe.stderr.log`：对应原采集程序输出；不是人为改写的诊断结论。
- `raw/r*/case.json`及`capture_manifest.json`：样本身份、BOOT身份、时钟域和冻结位置。
- `decoded/r*_startup.json`：由包内同一解码器从原始字解码的事件、首事件和计数。
- `tables/`：GP事件、HP首事件和104字逐字含义，CSV保留十进制／十六进制原值。
- `decoder/decode_ps_release.py`：实际解码逻辑，使用Python标准库；不访问板端。
- `decoder/ps_release_witness.sv`、`ai_read_monitor.sv`：实际记录器RTL，供核对采样／冻结／字布局；不是完整FPGA工程。

104字通道次序：0=HC0、1=HC1、2=HC2、3=HC3、4=S01视频入口、5=HP2互联对PS出口。
通道15号字表示按ARLEN累计的预期返回拍数，不能当作错误计数或完成证明。
首R管脚编码为`{RLAST,RRESP[1:0],RID[5:0]}`：r26为0x120，r29为0x20，二者RID均为32。

## VCD查看说明

`vcd/r*_GP_full.vcd`保留完整GP事件时间轴；`r*_GP_release_zoom.vcd`仅保留PL释放前40至后15个GP周期，适合直接查看。
缩放文件将左边界重设为时间0，`original_GP_cycle`保留原GP周期；`$timescale 10ns`来自名义GP100MHz。
VCD只包含已记录的同步电平变化，没有添加时钟、R握手脉冲或RDATA。缩放左端电平由此前最后一条记录保持而来。
完整记录首条事件之前及所有文件结束之后置X／`observation_valid=0`，表示不在覆盖范围。
可用支持VCD的波形查看器打开，但查看器中的曲线仍是事件记录重建，不能称为原生ILA采样。

## 主要信号对应关系

| 图中信号 | 实际观测边界／内部名称 |
|---|---|
| PS HP2 resetn | PS输出，经`diagnostic_ps_resetn`导出；不是PL给PS的复位输入 |
| PL HP2 resetn | `proc_sys_reset_1_peripheral_aresetn`，经`diagnostic_hp2_resetn`导出 |
| DDR calibrated | `ddr3_init_done`，PL侧MIG校准就绪 |
| PS ARVALID / RVALID | `axi_interconnect_4_M00_AXI_ARVALID/RVALID`，`diagnostic_hp2_read[60]/[62]` |
| S01 ARVALID / RVALID | 外围`S_AXI_HP2_ARVALID/RVALID`，原视频分支与互联之间 |

图中放大窗的GP先后关系不等于源域精确传播延迟。若进一步需要逐拍RREADY／ARREADY／RDATA及配置前事务，需要另行准备厂商适配支持的连续采样方案；本包没有伪造这些缺失信号。
'''
    (out/'README.md').write_text(notes,encoding='utf-8')
    support=out/'decoder';support.mkdir(exist_ok=True)
    shutil.copyfile(R/'FPGA/hdmi_candidate/software/decode_ps_release.py',support/'decode_ps_release.py')
    shutil.copyfile(R/'FPGA/hdmi_candidate/diagnostics/ps_release_witness.sv',support/'ps_release_witness.sv')
    shutil.copyfile(R/'FPGA/hdmi_candidate/baselines/ps_release_r26/sources/ai_read_monitor.sv',support/'ai_read_monitor.sv')
    archive.parent.mkdir(parents=True,exist_ok=True)
    if archive.exists():raise RuntimeError('Preserve existing delivery archive')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for path in sorted(out.rglob('*')):
            if path.is_file():z.write(path,arcname='HDMI_HP2_waveforms_20261022/'+path.relative_to(out).as_posix())
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix('.zip.sha256').write_text(digest+'  '+archive.name+'\n',encoding='ascii')
    print(json.dumps(dict(archive=str(archive),bytes=archive.stat().st_size,sha256=digest)))


def main():
    p=argparse.ArgumentParser();p.add_argument('--asset-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--zip',type=Path,required=True);a=p.parse_args()
    if a.output.exists() or a.zip.exists():raise RuntimeError('Fresh output paths required; preserve earlier export')
    a.output.mkdir(parents=True)
    cases={k:load_case(a.asset_root,a.output,k,d) for k,d in CASES.items()}
    if cases['r28']['meta']['BOOT_sha256']!=cases['r29']['meta']['BOOT_sha256']:raise RuntimeError('Comparison image differs')
    figures(cases,a.output)
    dump(a.output/'capture_manifest.json',dict(export_date='2026-10-22',description='Exact raw records + synchronized GP event reconstructions; no new experiment',
         cases={k:c['meta'] for k,c in cases.items()},raw_files='Copied byte-for-byte from retained board archives',
         clocks='Nominal constraints only; no measured clock waveform. GP and HP counts must not be directly aligned.',
         VCD='Recorded GP levels only; unknown before first observation and after capture. Zoom timestamps are rebased.'))
    finish_export(a.output,a.zip)
    print(json.dumps(dict(exported=str(a.output),cases=list(cases),raw_bytes=sum(p.stat().st_size for p in (a.output/'raw').rglob('*') if p.is_file()))))


if __name__=='__main__':main()
