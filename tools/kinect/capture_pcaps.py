"""Bounded SDK-free PC receiver for existing three-RX PCAP streams.

Does not configure radios, alter drivers, start an SDK, or create fake windows.
Packet receipt QPC is retained as receipt time, not RF capture time.
"""
import argparse
import ctypes
import json
from pathlib import Path
import selectors
import socket
import struct
import time

PEERS={'192.168.50.1':'rx1','192.168.50.3':'rx2','192.168.50.4':'rx3'}


def qpc():
    value=ctypes.c_longlong()
    if not ctypes.windll.kernel32.QueryPerformanceCounter(ctypes.byref(value)):raise OSError('QPC failed')
    return value.value


def capture(output,seconds,bind='192.168.50.49',port=39033,stop_file=None):
    if not 1<=seconds<=600 or bind!='192.168.50.49' or port!=39033:raise ValueError('Explicit finite existing-router endpoint required')
    output=Path(output);output.mkdir(exist_ok=False)
    counter_frequency=ctypes.c_longlong();ctypes.windll.kernel32.QueryPerformanceFrequency(ctypes.byref(counter_frequency))
    meta=dict(schema='KINECT-CSI-PCAP1',bind=bind,port=port,seconds=seconds,peers=PEERS,
        qpc_frequency_hz=counter_frequency.value,clock='same Windows QPC as Kinect host receipt brackets',
        RF_clock_synchronized=False,board_used=False,SDK=False,simulation=False)
    (output/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    selector=selectors.DefaultSelector();clients={};segments={p:0 for p in PEERS};totals={p:dict(bytes=0,packets=0,connections=0) for p in PEERS}
    listener=socket.socket();listener.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);listener.bind((bind,port));listener.listen(8);listener.setblocking(False)
    selector.register(listener,selectors.EVENT_READ,None)
    started=time.monotonic();last_report=0;failure=None;connections=[];ready_written=False
    print('Listening for existing RX services on '+bind+':'+str(port),flush=True)
    try:
        while time.monotonic()-started<seconds:
            if stop_file and Path(stop_file).exists():break
            for key,_ in selector.select(.1):
                if key.fileobj is listener:
                    sock,address=listener.accept();peer=address[0]
                    if peer not in PEERS or peer in clients:sock.close();continue
                    segments[peer]+=1;totals[peer]['connections']+=1
                    name=PEERS[peer]+'-'+str(segments[peer]).zfill(3)
                    state=dict(peer=peer,socket=sock,raw=(output/(name+'.pcap')).open('xb'),
                        rows=(output/(name+'-timing.jsonl')).open('x'),buffer=bytearray(),offset=0,index=0,
                        header=False,endian='<',tick_ns=1000,first_qpc=qpc(),name=name)
                    connections.append(state);clients[peer]=state;sock.setblocking(False);selector.register(sock,selectors.EVENT_READ,state)
                    print('Connected '+PEERS[peer]+' '+peer,flush=True)
                    continue
                state=key.data;begin=qpc()
                try:data=state['socket'].recv(65536)
                except ConnectionResetError:data=b''
                end=qpc()
                if not data:
                    selector.unregister(state['socket']);state['socket'].close();state['raw'].flush();state['rows'].flush();clients.pop(state['peer'],None);continue
                state['raw'].write(data);totals[state['peer']]['bytes']+=len(data);state['buffer'].extend(data)
                pending=state['buffer']
                if not state['header']:
                    if len(pending)<24:continue
                    magic=bytes(pending[:4]);formats={b'\xd4\xc3\xb2\xa1':('<',1000),b'\xa1\xb2\xc3\xd4':('>',1000),b'\x4d\x3c\xb2\xa1':('<',1),b'\xa1\xb2\x3c\x4d':('>',1)}
                    if magic not in formats:raise ValueError('Invalid original PCAP global header from '+state['peer'])
                    state['endian'],state['tick_ns']=formats[magic];state['header']=True;del pending[:24];state['offset']=24
                while len(pending)>=16:
                    sec,sub,length,original=struct.unpack_from(state['endian']+'IIII',pending)
                    if length>262144 or length>original:raise ValueError('Invalid captured record length')
                    if len(pending)<16+length:break
                    stamp=sec*1000000000+sub*state['tick_ns']
                    state['rows'].write(json.dumps(dict(packet=state['index'],pcap_offset=state['offset'],capture_ns=stamp,
                        host_recv_begin_qpc=begin,host_recv_end_qpc=end,record_bytes=16+length))+'\n')
                    state['offset']+=16+length;state['index']+=1;totals[state['peer']]['packets']+=1;del pending[:16+length]
                if sum(v['bytes'] for v in totals.values())>4*1024**3:raise ValueError('Finite 4 GiB capture budget reached')
            if not ready_written and all(v['packets']>0 for v in totals.values()):
                (output/'ready.json').write_text(json.dumps(dict(host_qpc=qpc(),all_three_received=True))+'\n');ready_written=True
            elapsed=time.monotonic()-started
            if elapsed-last_report>=3:
                last_report=elapsed;print(json.dumps(dict(seconds=round(elapsed,1),receivers={PEERS[p]:v for p,v in totals.items()})),flush=True)
                for state in connections:state['raw'].flush();state['rows'].flush()
    except KeyboardInterrupt:failure='user_cancelled'
    except Exception as error:failure=repr(error);raise
    finally:
        for state in connections:
            try:selector.unregister(state['socket'])
            except Exception:pass
            state['socket'].close();state['raw'].close();state['rows'].close()
        selector.close();listener.close()
        report=dict(elapsed_seconds=time.monotonic()-started,receivers={PEERS[p]:v for p,v in totals.items()},
            all_three_received=all(v['packets']>0 for v in totals.values()),error=failure,
            segments=[dict(name=s['name'],peer=s['peer'],complete_packets=s['index'],trailing_bytes=len(s['buffer'])) for s in connections],sockets_closed=True)
        (output/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);p.add_argument('--seconds',type=int,default=30);p.add_argument('--stop-file',type=Path)
    a=p.parse_args();report=capture(a.output,a.seconds,stop_file=a.stop_file)
    if not report['all_three_received']:raise SystemExit(3)
