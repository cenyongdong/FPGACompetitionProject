"""Read-only Lite boot/interface audit. Run with Python 3 on the board.

Reads the FAT16 boot partition directly without mounting or modifying it.
Never opens /dev/mem, the FPGA manager firmware interface, or video devices.
"""
import hashlib
import json
import os
import struct
import base64
import textwrap
import subprocess
from pathlib import Path


def audit_fat16(path):
    with open(path, 'rb', buffering=0) as dev:
        def read_at(offset, size):
            dev.seek(offset)
            data = dev.read(size)
            if len(data) != size:
                raise ValueError('Short partition read')
            return data
        b = read_at(0, 512)
        bps = struct.unpack_from('<H', b, 11)[0]
        spc = b[13]
        reserved = struct.unpack_from('<H', b, 14)[0]
        fats = b[16]
        entries = struct.unpack_from('<H', b, 17)[0]
        sectors = struct.unpack_from('<H', b, 19)[0] or struct.unpack_from('<I', b, 32)[0]
        fat_sectors = struct.unpack_from('<H', b, 22)[0]
        if b[510:512] != b'\x55\xaa' or bps != 512 or not spc or not entries or not fat_sectors:
            raise ValueError('Unsupported FAT boot sector; stop rather than guess')
        root_sectors = (entries * 32 + bps - 1) // bps
        root_offset = (reserved + fats * fat_sectors) * bps
        data_offset = root_offset + root_sectors * bps
        cluster_count = (sectors - data_offset // bps) // spc
        if not 4085 <= cluster_count < 65525:
            raise ValueError('Partition is not FAT16')
        fat = read_at(reserved * bps, fat_sectors * bps)
        root = read_at(root_offset, entries * 32)
        files = []
        for off in range(0, len(root), 32):
            e = root[off:off+32]
            if e[0] == 0:
                break
            if e[0] == 0xe5 or e[11] & 0x18 or e[11] == 0x0f:
                continue
            base = e[:8].decode('ascii', 'replace').rstrip()
            ext = e[8:11].decode('ascii', 'replace').rstrip()
            name = base + ('.' + ext if ext else '')
            cluster = struct.unpack_from('<H', e, 26)[0]
            size = struct.unpack_from('<I', e, 28)[0]
            if size > 128 * 1024 * 1024:
                raise ValueError('Unexpectedly large boot file')
            left, chunks, seen = size, [], set()
            while left:
                if cluster in seen or not 2 <= cluster < cluster_count + 2:
                    raise ValueError('Invalid FAT cluster chain: ' + name)
                seen.add(cluster)
                n = min(left, spc * bps)
                chunks.append(read_at(data_offset + (cluster - 2) * spc * bps, n))
                left -= n
                cluster = struct.unpack_from('<H', fat, cluster * 2)[0]
            data = b''.join(chunks)
            item = dict(name=name, size=size, sha256=hashlib.sha256(data).hexdigest(), head_hex=data[:32].hex())
            if name.upper() == 'UENV.TXT':
                item['text'] = data.decode('utf-8', 'replace')
            files.append(item)
        return dict(files=files, fat_type='FAT16', bytes_per_sector=bps, sectors_per_cluster=spc)


def read_text(path):
    try:
        return Path(path).read_bytes().replace(b'\0', b' ').decode('utf-8', 'replace').strip()
    except OSError:
        return None


def main():
    report = {'scope': 'read-only; no mount, register access, model, encode, or configuration write',
              'uname': list(os.uname()), 'cmdline': read_text('/proc/cmdline'),
              'fpga_state': read_text('/sys/class/fpga_manager/fpga0/state'),
              'video_name': read_text('/sys/class/video4linux/video0/name'),
              'udmabuf_bytes': read_text('/sys/class/u-dma-buf/udmabuf0/size')}
    packages = subprocess.run(['dpkg-query', '-W', '-f=${Package}\t${Architecture}\t${Version}\n'],
                              capture_output=True, text=True, timeout=15)
    report['package_query_returncode'] = packages.returncode
    report['runtime_packages'] = [line for line in packages.stdout.splitlines()
                                 if any(key in line.lower() for key in ('icraft', 'customop'))]
    report['video_driver'] = os.path.realpath('/sys/class/video4linux/video0/device/driver')
    report['device_nodes_present'] = [path for path in ('/dev/udmabuf0', '/dev/video0', '/dev/mem')
                                      if Path(path).exists()]
    try:
        report['boot_partition'] = audit_fat16('/dev/mmcblk0p1')
    except Exception as exc:
        report['boot_partition_error'] = str(exc)
    report['device_tree'] = []
    for root, dirs, files in os.walk('/sys/firmware/devicetree/base'):
        compatible = read_text(root + '/compatible')
        if any(s in (root + ' ' + (compatible or '')).lower()
               for s in ('fpga', 'hdmi', 'udma', 'aiu', 'zg330', 'vpu', 'mvx', 'video', 'allegro')):
            report['device_tree'].append({'path': root, 'compatible': read_text(root + '/compatible'),
                                          'status': read_text(root + '/status'),
                                          'reg_hex': Path(root + '/reg').read_bytes().hex()
                                          if Path(root + '/reg').is_file() else None})
    # Bounded ASCII lines preserve exact evidence through a Windows PTY.
    encoded = base64.b64encode(json.dumps(report, ensure_ascii=True).encode()).decode()
    print('POSE_AUDIT_BEGIN')
    print(textwrap.fill(encoded, width=64))
    print('POSE_AUDIT_END')


if __name__ == '__main__':
    main()
