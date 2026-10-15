"""Prepare a fresh, bounded HDMI read-only probe; no hardware initialization."""
from pathlib import Path
import hashlib
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
revision = sys.argv[1] if len(sys.argv)>1 else 'r1'
assert revision in ('r1', 'r2')
namespace = 'hdmi-stage1-20261015-' + revision
E = ROOT / 'tools/pose-v1/evidence' / namespace
E.mkdir(exist_ok=False)
(E / 'before').mkdir()
for name in ('Done.md', 'DIFFICULTIES.md', 'PROJECT-PROGRESS.md', 'REFERENCES.md', 'ARCHITECTURE-DISCUSSION-20261015.md'):
    shutil.copyfile(ROOT / name, E / 'before' / name)

preflight = (ROOT / 'tools/pose-v1/board_application_preflight.py').read_text(encoding='utf-8')
functions = preflight[:preflight.index('out=pathlib.Path(sys.argv[1])')]
inventory = (ROOT / 'tools/pose-v1/hdmi_readonly_audit.py').read_text(encoding='utf-8')
inventory = inventory.replace("out=Path(sys.argv[1]);assert not out.exists()", "out=None")
inventory = inventory[:inventory.index('out.write_bytes(')]
extra = '''
report['recorded_at_utc']=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
report['scope']='read_only_no_MMIO_SDK_ioctl_mount_or_device_initialization; boot partition opened rb only'
report['identity']={'boot_files':fat_files(),'libraries':{n:digest('/usr/lib/aarch64-linux-gnu/'+n) for n in ('libicraft_hostbackend.so','libicraft_zg330backend.so','libicraft_xrt.so')},'packages':subprocess.check_output(['dpkg-query','-W','-f=${Package} ${Architecture} ${Version}\\n','icraft:arm64','customop:arm64'],text=True,timeout=10).splitlines()}
report['uname']=list(os.uname())
report['processes']=subprocess.check_output(['ps','-eo','pid,comm'],text=True,timeout=10)
report['kernel_log_at_end_of_probe']=subprocess.check_output(['dmesg'],timeout=10).decode(errors='replace')
report['boot_id']=read('/proc/sys/kernel/random/boot_id')
report['mounts']=read('/proc/mounts')
report['i2c_adapter_names']={p.name:read(p/'name') for p in Path('/sys/class/i2c-adapter').glob('*')}
print(json.dumps(report,indent=2))
'''
(E / 'remote_probe.py').write_text(functions + '\n' + inventory + '\n' + extra, encoding='utf-8', newline='\n')
cache = ROOT / '.local' / namespace
cache.mkdir(exist_ok=False)
source = ROOT / '.local/shared-stability-transport-20261015-r2/secure_transport.py'
transport = source.read_text(encoding='utf-8').replace('/tmp/wifi-pose-shared-stability-20261015-r2/', '/tmp/'+namespace+'/')
(cache / 'secure_transport.py').write_text(transport, encoding='utf-8', newline='\n')
(E / 'transport-source.sha256.json').write_text(json.dumps({'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'copy_sha256':hashlib.sha256((cache/'secure_transport.py').read_bytes()).hexdigest(),'only_change':'transfer namespace; only ssh used in this stage'},indent=2)+'\n',encoding='utf-8')
print('Fresh probe prepared:', E)
