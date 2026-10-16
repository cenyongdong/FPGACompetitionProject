"""Offline rollback identity and honest interpretation of scan results."""
from pathlib import Path
import hashlib, json, importlib.util, shutil, re
R=Path(__file__).resolve().parents[3];E=R/'tools/pose-v1/evidence/hdmi-board-reference-20261016-r1'
def sha(b):return hashlib.sha256(b).hexdigest()
audit=json.loads((R/'tools/pose-v1/evidence/boot-25122301-comparison-resolved.json').read_text(encoding='utf-8-sig'))
source=Path(audit['source_dir']);boot=(source/'BOOT.bin').read_bytes();bit=(source/'ai7030_top_disable_icap.bit').read_bytes()
spec=importlib.util.spec_from_file_location('selected_boot',R/'tools/pose-v1/inspect_selected_boot.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
payload,header=module.bit_payload(bit)
part=audit['pl_partition_from_supplied_log'];offset=part['byte_offset'];length=part['bytes']
raw=boot[offset:offset+length];swapped=b''.join(raw[i:i+4][::-1] for i in range(0,len(raw),4))
current=json.loads((E/'host-permission-r2/board-audit.json').read_text())
assert sha(boot)==current['BOOT']['sha256']==audit['source_boot_sha256']
assert swapped[:len(payload)]==payload and len(raw)==length
dest=E/'rollback';dest.mkdir(exist_ok=False);shutil.copyfile(source/'ai7030_top_disable_icap.bit',dest/'ai7030_top_disable_icap.bit')
assert sha((dest/'ai7030_top_disable_icap.bit').read_bytes())==sha(bit)
record={'source_directory':str(source),'BOOT_sha256':sha(boot),'board_BOOT_match':True,
 'rollback_bit_sha256':sha(bit),'rollback_bit_bytes':len(bit),'bit_header':header,
 'BOOT_PL_offset_bytes':offset,'BOOT_PL_bytes':length,'word_swapped_payload_prefix_equal':True,
 'padding_bytes':len(swapped)-len(payload),'runtime_jtag_reload_qualified':False,
 'limitation':'Identity verified against selected BOOT partition, not proof of safe hot replacement or full configuration readback'}
(E/'rollback-identity.json').write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
scans=[]
for name in ['chain-scan','chain-scan-host-permission-r2']:
 log=(E/name/'stdout.log').read_text(errors='replace')
 count=re.search(r'(\d+) cable is connected',log)
 scans.append({'directory':name,'cable_count':int(count.group(1)) if count else None,
  'actual_expected_serial_detected':bool(re.search(r'serial number\s*:\s*210512180081',log)),
  'FTDI_missing':'There are no FTDI chip found' in log,
  'raw_helper_flag_correction':'expected_cable_present merely matched echoed requested serial; this review uses enumeration output'})
(E/'chain-review.json').write_text(json.dumps(scans,indent=2)+'\n')
shutil.copyfile(Path(__file__),E/Path(__file__).name)
print(json.dumps({'rollback_BOOT_payload_verified':True,'rollback_SHA':sha(bit),'scans':scans},indent=2))
