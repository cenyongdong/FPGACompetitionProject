"""Pre-captured raw CSI -> existing PIWCSI1 TCP contract; no GT/inference."""
from pathlib import Path
import hashlib, json, re, socket, sys, time

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/pose-v1'))
from csi_io import load_mat, encode_window

DEFAULT_DATA=Path(r'D:\Person-in-WIFI-3D\Person-in-WiFi-3D-repo\data\wifipose')
def prepare(data:Path, output:Path, frames:int, sequence:str=''):
    assert 1<=frames<=100
    folder=data/'test_data/csi' if (data/'test_data/csi').is_dir() else data
    def order(p): return tuple(int(s) if s.isdigit() else s for s in re.split(r'(\d+)',p.stem))
    files=sorted((p for p in folder.glob('*.mat') if not sequence or p.stem.startswith(sequence+'_')),key=order)
    if not files: raise ValueError('No CSI MAT files in '+str(folder))
    output.mkdir();catalog=[];payloads=[]
    for i in range(frames):
        source=files[i%len(files)];raw=encode_window(load_mat(source),1000000+i,0)
        assert len(raw)==86432
        payload=raw[32:];(output/f'{i}.payload').write_bytes(payload);payloads.append(payload)
        catalog.append({'sequence':i,'frame_id':1000000+i,'source_file':str(source.resolve()),
                        'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                        'payload_sha256':hashlib.sha256(payload).hexdigest()})
    (output/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n',encoding='utf-8')
    return catalog,payloads

def send(host,port,hz,catalog,payloads,out,viewer):
    assert 0.5<=hz<=2 and len(payloads)/hz<=55
    deadline=time.perf_counter()+90
    if viewer:
        while not (out/'viewer.ready').exists():
            if (out/'stop.request').exists():raise RuntimeError('Controller cancelled host startup')
            if viewer.poll() is not None:raise RuntimeError('Viewer exited before first decoded RTSP frame')
            if time.perf_counter()>=deadline:raise TimeoutError('First decoded RTSP frame timeout')
            time.sleep(.1)
    # Only refused startup connects may be attempted again; never reconnect a
    # CSI session after it has been accepted, and never resend input records.
    while True:
        if (out/'stop.request').exists():raise RuntimeError('Controller cancelled input startup')
        try:connection=socket.create_connection((host,port),1);break
        except (ConnectionRefusedError,TimeoutError):
            if time.perf_counter()>=deadline:raise TimeoutError('Input listener startup timeout')
            time.sleep(.1)
    sent=[]
    try:
        connection.settimeout(5);connection.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
        epoch=time.perf_counter();(out/'sender.started').write_text(str(time.perf_counter_ns())+'\n')
        import struct
        for row,payload in zip(catalog,payloads):
            if (out/'stop.request').exists():raise RuntimeError('Controller cancelled replay')
            planned=epoch+row['sequence']/hz
            delay=planned-time.perf_counter()
            if delay>0:time.sleep(delay)
            if time.perf_counter()-planned>.2:raise TimeoutError('Replay missed slot; no catch-up burst')
            if viewer and viewer.poll() is not None:raise RuntimeError('Viewer stopped while CSI was active')
            stamp=time.perf_counter_ns();header=struct.pack('<8sIIQQ',b'PIWCSI1\0',1,86400,row['frame_id'],stamp)
            connection.sendall(header+payload)
            sent.append(dict(row,source_time_ns=stamp,send_end_pc_ns=time.perf_counter_ns()))
        connection.shutdown(socket.SHUT_WR)
    finally:
        connection.close();(out/'sent.json').write_text(json.dumps({'hz':hz,'records':sent,'sent_is_not_receiver_ack':True},indent=2)+'\n',encoding='utf-8')
        (out/'sender.finished').write_text(str(len(sent))+'\n')
    return sent
