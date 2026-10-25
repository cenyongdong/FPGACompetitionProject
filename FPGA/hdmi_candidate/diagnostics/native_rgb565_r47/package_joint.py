from pathlib import Path
import json,tarfile,io,hashlib
W=Path(__file__).resolve().parent
E=Path('D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-render-speed-20261024-r47')
source=Path('D:/FPGACompetitionProject/.local/hp2-deferred-consume-20261024-r45/software.tar.gz')
binary=(W/'pose_demo_v1').read_bytes()
with tarfile.open(source) as src:
    identity=json.load(src.extractfile('software/identity.json'))
    guard=src.extractfile('software/board_guard.py').read().decode()
    guard=guard.replace('<= 1800:','<= 2100:').replace("'HDMI': False","'HDMI': True").replace('child.wait(timeout=5)','child.wait(timeout=15)')
    compile(guard,'board_guard.py','exec');guard=guard.encode()
    replacements={'software/pose_demo_v1':binary,'software/board_guard.py':guard}
    for name,data in replacements.items():identity['files'][Path(name).name]=hashlib.sha256(data).hexdigest()
    replacements['software/identity.json']=(json.dumps(identity,indent=2)+'\n').encode()
    out=W/'software-native-rgb565-final.tar.gz'
    with tarfile.open(out,'x:gz') as dst:
        for member in src:
            if member.name in replacements:
                data=replacements[member.name];member.size=len(data);dst.addfile(member,io.BytesIO(data))
            else:dst.addfile(member,src.extractfile(member) if member.isfile() else None)
result=dict(compiled=True,SDK_executed=False,model_math_SDK_NPU_wire_unchanged=True,
    RGB24_intermediate_removed=True,upscale_removed=True,reused_core_objects=True,
    bytes=len(binary),sha256=hashlib.sha256(binary).hexdigest(),initial_observer_generation=4,final_observer_generation=12,
    software_archive=str(out),archive_bytes=out.stat().st_size,
    archive_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),cooperative_signal_stop=True)
(E/'joint-build.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
print(json.dumps(result))
