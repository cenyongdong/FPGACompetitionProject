"""Apply an explicit bounded resource choice and return its evidence."""
from pathlib import Path
import getpass,hashlib,json,sys
import ssh_memory_transport as t
from archive_bytes import extract_bytes
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-address-20261011-r2';remote='/tmp/pose-producer-address-20261011-r2'
mode=sys.argv[1];assert mode in ('audit','compact-once');assert json.loads((E/'off.data-review.json').read_text())['calls']==100
source=R/'tools/pose-v1/producer_address_resources.py';secret=getpass.getpass('Authorized Lite password (memory only): ');prompt=t.getpass.getpass;t.getpass.getpass=lambda _:secret
def call(*args):
    sys.argv=['transport',*map(str,args)]
    try:t.main()
    except SystemExit as e:return e.code or 0
    return 0
try:
    assert call('put',source,remote+'/producer_address_resources.py','--log',E/'resource-upload.txt')==0
    h=hashlib.sha256(source.read_bytes()).hexdigest()
    cmd='set -eu; cd '+remote+'; echo "'+h+'  producer_address_resources.py" | sha256sum -c -; python3 producer_address_resources.py '+mode+'; tar -cf return-resources.tar resources-on'
    assert call('ssh',cmd,'--log',E/'resource-operation.txt')==0
    assert call('get',remote+'/return-resources.tar',E/'return-resources.tar','--log',E/'resource-download.txt')==0
    extract_bytes(E/'return-resources.tar',E/'resources-return');d=E/'resources-return/resources-on'
    for line in (d/'files.sha256').read_text().splitlines():h,n=line.split('  ',1);assert hashlib.sha256((d/n).read_bytes()).hexdigest()==h
    assert (d/'before.dmesg.txt').read_bytes()==(d/'after.dmesg.txt').read_bytes()
    print('Resource decision returned:',(d/'review.json').read_text())
finally:secret='';t.getpass.getpass=prompt
