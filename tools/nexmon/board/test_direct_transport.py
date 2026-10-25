"""Linux-only SDK-free TCP checks using one frozen three-receiver recording."""
import argparse
import array
import json
from pathlib import Path
import queue
import socket
import struct
import subprocess
import threading
import time


def check(build, fixtures, output):
    output.mkdir()
    files = [(fixtures / (str(i)+'.pcap')).read_bytes() for i in range(3)]
    result = []

    def start(name):
        folder = output/name
        probe = socket.socket(); probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]; probe.close()
        process = subprocess.Popen([str(build/'csi_direct_receiver'), '--bind', '127.0.0.1',
            '--peers', '127.0.0.2,127.0.0.3,127.0.0.4', '--port', str(port),
            '--session', 'one-frozen-job', '--source', 'f0:2f:74:39:45:6c',
            '--channel', '0xd0a1', '--gains', '1,2,3', '--output', str(folder),
            '--seconds', '8', '--simulation'], stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True)
        lines, incoming = [], queue.Queue()
        def reader():
            for line in process.stdout:
                lines.append(line); incoming.put(line)
        reader_thread = threading.Thread(target=reader); reader_thread.start()
        first = incoming.get(timeout=4)
        assert json.loads(first)['pc_required'] is False
        return process, folder, port, lines, reader_thread

    def finish(process, folder, lines, reader_thread, expected=0):
        process.wait(timeout=12)  # executable owns its independent 8-second finite budget
        reader_thread.join(timeout=2)
        stderr = process.stderr.read()
        (folder/'native.stdout').write_text(''.join(lines))
        (folder/'native.stderr').write_text(stderr)
        assert (process.returncode == 0) == (expected == 0), (process.returncode, stderr)
        return stderr

    def send(index, port, data, errors):
        try:
            with socket.socket() as client:
                client.bind(('127.0.0.'+str(index+2),0))
                client.connect(('127.0.0.1',port))
                position, n = 0, 0
                while position < len(data):
                    length = (1,13,997,32767)[n % 4]
                    client.sendall(data[position:position+length]); position += length; n += 1
                client.shutdown(socket.SHUT_WR)
        except Exception as error:
            errors.append(repr(error))

    process, folder, port, lines, reader_thread = start('positive')
    errors = []
    threads = [threading.Thread(target=send, args=(i,port,data,errors)) for i,data in enumerate(files)]
    for thread in threads: thread.start()
    for thread in threads: thread.join(timeout=8)
    assert not any(thread.is_alive() for thread in threads)
    assert not errors, errors
    finish(process,folder,lines,reader_thread)
    summary = json.loads((folder/'summary.json').read_text())
    assert summary['windows']==120 and summary['enumerated']==134 and summary['common_events']==2988
    assert summary['inferences']==0 and summary['loopback_simulation']
    assert any('first_window_emitted_before_eof' in line for line in lines)
    for i,data in enumerate(files): assert (folder/('rx'+str(i+1)+'.pcap')).read_bytes()==data

    reference, ledger = output/'reference.piwcsi2', output/'reference.json'
    subprocess.run([str(build/'nexmon_replay'), '--session', 'one-frozen-job',
        '--source-mac', 'f0:2f:74:39:45:6c', '--channel', '0xd0a1', '--gains','1','2','3',
        '--pcaps', *[str(fixtures/(str(i)+'.pcap')) for i in range(3)],
        '--output',str(reference),'--report',str(ledger)],check=True,capture_output=True)
    actual, expected = (folder/'windows.piwcsi2').read_bytes(), reference.read_bytes()
    assert len(actual)==len(expected)==120*86432
    for offset in range(0,len(actual),86432):
        assert actual[offset:offset+24]==expected[offset:offset+24]
        assert struct.unpack_from('<Q',actual,offset+24)[0]>0
        assert actual[offset+32:offset+86432]==expected[offset+32:offset+86432]
    tokens=array.array('f');tokens.frombytes((folder/'tokens.f32').read_bytes())
    assert len(tokens)==120*10800
    amplitude_values=0
    for frame in range(120):
        values=array.array('d');values.frombytes(actual[frame*86432+32:(frame+1)*86432])
        for token in range(180):
            for carrier in range(30):
                at=(token*30+carrier)*2
                magnitude=abs(complex(values[at],values[at+1]))
                expected_f32=struct.unpack('<f',struct.pack('<f',magnitude))[0]
                assert tokens[frame*10800+token*60+carrier]==expected_f32
                amplitude_values += 1
    result.append(dict(test='three-stream-segmentation',windows=120,raw_streams_exact=True,
        all_csi_payloads_exact=True,amplitude_features_exact=amplitude_values,
        first_window_before_eof=True,model_executed=False))

    process, folder, port, lines, reader_thread = start('truncated')
    errors=[]
    threads=[threading.Thread(target=send,args=(i,port,data[:-1] if i==2 else data,errors))
             for i,data in enumerate(files)]
    for thread in threads:thread.start()
    for thread in threads:thread.join(timeout=8)
    stderr=finish(process,folder,lines,reader_thread,1)
    assert 'Truncated PCAP' in stderr
    result.append(dict(test='truncated-peer-stream',rejected=True,original_partial_preserved=True))

    process, folder, port, lines, reader_thread = start('unexpected')
    with socket.socket() as client:
        client.bind(('127.0.0.5',0));client.connect(('127.0.0.1',port))
        stderr=finish(process,folder,lines,reader_thread,1)
    assert 'Unexpected receiver' in stderr
    result.append(dict(test='unexpected-peer',rejected=True))

    process, folder, port, lines, reader_thread = start('duplicate')
    clients=[]
    try:
        for _ in range(2):
            client=socket.socket();client.bind(('127.0.0.2',0));client.connect(('127.0.0.1',port));clients.append(client)
        stderr=finish(process,folder,lines,reader_thread,1)
    finally:
        for client in clients:client.close()
    assert 'Duplicate receiver' in stderr
    result.append(dict(test='duplicate-peer',rejected=True))
    (output/'checks.json').write_text(json.dumps(dict(checks=result,board_execution=False,
        sdk_execution=False,router_live_test=False),indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--fixtures',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(check(args.build,args.fixtures,args.output)))
