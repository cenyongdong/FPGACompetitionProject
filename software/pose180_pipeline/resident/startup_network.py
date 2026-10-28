"""Temporary board CSI address; preserve every pre-existing network setting."""
import json
from pathlib import Path
import socket
import struct
import subprocess
import time

ADDRESS = '192.168.50.49'
INTERFACE = 'eth0'


def add():
    before = json.loads(subprocess.check_output(['ip', '-j', 'addr', 'show', 'dev', INTERFACE]))
    if any(item['local'] == ADDRESS for interface in before for item in interface['addr_info']):
        return dict(added=False, address=ADDRESS+'/24', interface=INTERFACE)
    mac = bytes.fromhex(Path('/sys/class/net/'+INTERFACE+'/address').read_text().strip().replace(':', ''))
    request = (b'\xff'*6 + mac + b'\x08\x06' + struct.pack('!HHBBH', 1, 0x0800, 6, 4, 1)
               + mac + b'\0'*4 + b'\0'*6 + socket.inet_aton(ADDRESS))
    with socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0806)) as channel:
        channel.bind((INTERFACE, 0))
        channel.settimeout(.1)
        for _ in range(3):
            channel.send(request)
            end = time.monotonic()+.4
            while time.monotonic() < end:
                try:
                    data = channel.recv(2048)
                except socket.timeout:
                    continue
                if (len(data) >= 42 and data[12:14] == b'\x08\x06' and data[22:28] != mac
                        and data[28:32] == socket.inet_aton(ADDRESS)):
                    raise ValueError('CSI address already owned by another device')
    subprocess.run(['ip', 'addr', 'add', ADDRESS+'/24', 'dev', INTERFACE], check=True)
    return dict(added=True, address=ADDRESS+'/24', interface=INTERFACE)


def remove(receipt):
    if receipt.get('added'):
        subprocess.run(['ip', 'addr', 'del', receipt['address'], 'dev', receipt['interface']], check=True)
