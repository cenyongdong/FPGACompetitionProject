"""Summarize the actual failed first trial and verified original-BOOT recovery."""
from pathlib import Path
import datetime
import json
import tarfile

ROOT=Path(__file__).resolve().parents[3]
WORK=ROOT/'.local/hdmi-probe-free-20261025-r1'
E=ROOT/'tools/pose-v1/evidence/hdmi-probe-free-20261025-r1'
out=WORK/'board-evidence-round-1'
out.mkdir(exist_ok=False)
with tarfile.open(WORK/'round-1-result-evidence.tar.gz') as archive:
    for member in archive.getmembers():
        target=(out/member.name).resolve()
        if not target.is_relative_to(out):raise ValueError('Archive path escaped evidence directory')
        if member.issym() and member.name=='pipeline/models':continue
        if member.isdir():target.mkdir(parents=True,exist_ok=True)
        elif member.isfile():
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(archive.extractfile(member).read())
        else:raise ValueError('Unexpected evidence member')
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
meta=out/'boot-control/metadata'
closed=read(meta/'closed.json');audit=read(meta/'final-audit.json')
trial=read(meta/'long-test.json');failure=read(out/'pipeline/run/engine/failure.json')
assert closed['closed'] and closed['SDK_Open_attempts']==1
assert trial['native_exit']==3 and trial['native_shutdown_complete'] and not trial['device_owners']
assert not audit['device_owners'] and audit['boot_id']==closed['boot_id']
assert failure['stage']=='initialization' and failure['invocation']==0
for tag in ('candidate-1','fallback'):
    assert read(WORK/('uart-'+tag)/'reader.json')['closed']
network=read(WORK/'pc-network-restored.json')
assert network['restored'] and network['original_retained']
for role in ('tx','rx3'):
    assert read(WORK/'router-receipts'/role/'restore-ssh.json')['sshd_enable']=='0'
state=dict(package_id=WORK.name,status='closed_SDK_initialization_failed',closed=True,
    physical_qualification=read(E/'qualification.json')['bit_generation_prerequisite_pass'],
    candidate_BOOT_sha256=read(E/'package-review.json')['sha256'],
    candidate_boot_id=read(meta/'startup.json')['boot_id'],current_boot_id=closed['boot_id'],
    current_BOOT_sha256=audit['startup_files']['BOOT.BIN']['sha256'],running_original_BOOT=True,
    candidate_promoted=False,consumed=dict(candidate_starts=1,SDK_Open=1,original_fallbacks=1),
    cancelled_rounds=[2,3],remaining=dict(candidate_starts=0,SDK_Open=0,original_fallbacks=0),
    native_exit=trial['native_exit'],actual_seconds=trial['seconds'],
    inference_count=trial['final_status']['inferred'],HDMI_adoptions=trial['final_status']['adopted'],
    SDK_failure_stage=failure['stage'],native_shutdown_complete=True,device_owners=[],
    routers_autostart_preserved=True,router_test_loads=0,temporary_access_restored=True,
    active_owned_work=False,board_evidence=str(out),
    recorded_at=datetime.datetime.now().astimezone().isoformat())
(E/'state.json').write_text(json.dumps(state,indent=2)+'\n')
print(json.dumps(state))
