"""Execute one explicitly chosen compaction and return its full snapshots."""
from pathlib import Path
import getpass,sys,json,hashlib,tarfile
import ssh_memory_transport as t
from archive_bytes import extract_bytes
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-vpu-20261011-r2';remote='/tmp/pose-producer-vpu-20261011-r2';source=R/'tools/pose-v1/producer_vpu_resources.py'
assert json.loads((E/'off.data-review.json').read_text())['calls']==100
secret=getpass.getpass('Authorized Lite password (memory only): ');prompt=t.getpass.getpass;t.getpass.getpass=lambda _:secret
def call(*args):
    sys.argv=['transport',*map(str,args)]
    try:t.main()
    except SystemExit as e:return e.code or 0
    return 0
try:
    assert call('put',source,remote+'/producer_vpu_resources.py','--log',E/'resource-upload.txt')==0
    h=hashlib.sha256(source.read_bytes()).hexdigest()
    cmd='set -eu; cd '+remote+'; echo "'+h+'  producer_vpu_resources.py" | sha256sum -c -; python3 producer_vpu_resources.py compact-once; tar -cf return-resources-on.tar resources-on'
    assert call('ssh',cmd,'--log',E/'resource-operation.txt')==0
    assert call('get',remote+'/return-resources-on.tar',E/'return-resources-on.tar','--log',E/'resource-download.txt')==0
    out=E/'resources-return';extract_bytes(E/'return-resources-on.tar',out);d=out/'resources-on'
    for line in (d/'files.sha256').read_text().splitlines():h,n=line.split('  ',1);assert hashlib.sha256((d/n).read_bytes()).hexdigest()==h
    r=json.loads((d/'review.json').read_text());assert r['writes']==1 and not r['drop_caches'] and not r['reboot'] and not r['CMA_changed']
    assert (d/'before.dmesg.txt').read_bytes()==(d/'after.dmesg.txt').read_bytes()
    print('One compaction recorded',r['elapsed_ns']/1e6,'ms; ordinary units',r['before_units512KiB'],'to',r['after_units512KiB'])
finally:secret='';t.getpass.getpass=prompt
