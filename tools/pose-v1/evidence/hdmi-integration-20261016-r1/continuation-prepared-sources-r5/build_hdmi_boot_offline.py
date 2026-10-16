"""Build the reviewed HDMI BOOT locally; never access the board or boot media."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

R = Path(__file__).resolve().parents[3]
E = R / 'tools/pose-v1/evidence/hdmi-integration-20261016-r1'
OLD = R / 'tools/pose-v1/evidence/hdmi-board-reference-20261016-r1'
W = R / '.local/hdmi-integration-20261016-r1/boot-offline-r5'
D = E / 'boot-offline-r5'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


review = json.loads((E / 'candidate-bit-r5/review.json').read_text(encoding='utf-8'))
assert review['payload_differs_from_original_BOOT']
assert review['Procise_execution']['exit'] == 0
assert json.loads((E / 'system-route-r5/review.json').read_text())['bit_generation_prerequisite_pass']
rollback = json.loads((OLD / 'rollback-identity.json').read_text(encoding='utf-8'))
source = Path(rollback['source_directory'])
control_ids = json.loads((OLD / 'boot-control-utf8-r2/inputs.json').read_text(encoding='utf-8'))
original = (source / 'BOOT.bin').read_bytes()
assert sha(original) == rollback['BOOT_sha256'] == 'ff350477e624c50d2f8180fb4b9130ec7688fbc7ca553412ed7c3dd2a68b31ef'
candidate = E / 'candidate-bit-r5/hdmi-integrated-r5_disable_icap.bit'
expected = review['products'][candidate.name]
assert sha(candidate.read_bytes()) == expected['sha256']
sys.path.insert(0, str(R / 'tools/pose-v1'))
from inspect_selected_boot import bit_payload
payload, _ = bit_payload(candidate.read_bytes())
assert sha(payload) == review['new_payload_sha256']
W.mkdir(exist_ok=False)
D.mkdir(exist_ok=False)
inputs = {}
for name in ['FSBL251210_ddr400_demo.out', 'bl31.elf', 'u-boot']:
    data = (source / name).read_bytes()
    assert sha(data) == control_ids[name]['sha256'], name
    (W / name).write_bytes(data)
    inputs[name] = {'source': str(source / name), 'bytes': len(data), 'sha256': sha(data)}
# Keep the original image name so the BOOT image-name table is unchanged.
shutil.copyfile(candidate, W / 'ai7030_top_disable_icap.bit')
inputs['ai7030_top_disable_icap.bit'] = {'source': str(candidate), **expected}
dump(D / 'inputs.json', inputs)
bif = '''//arch = fmql; split = false; format = BIN
the_ROM_image:
{
 [bootloader, destination_device = ps]@/FSBL251210_ddr400_demo.out
 [destination_device = pl]@/ai7030_top_disable_icap.bit
 [destination_cpu = apu_0, destination_device = ps]@/bl31.elf
 [destination_cpu = apu_0, destination_device = ps]@/u-boot
 [fsbl_config]apu_x32
}
'''.replace('@', W.as_posix())
(D / 'candidate.bif').write_text(bif, encoding='ascii')
shutil.copyfile(D / 'candidate.bif', W / 'candidate.bif')
output = W / 'BOOT-hdmi-r5.bin'
code = ('if {[catch {\n create_boot_image {' + (W / 'candidate.bif').as_posix() + '} {' + output.as_posix() +
        '} -fmql\n puts "HDMI_OFFLINE_BOOT_COMMAND_RETURNED"\n} result]} {puts "HDMI_OFFLINE_BOOT_FAILED $result";exit 1}\nexit\n')
(D / 'build.tcl').write_text(code, encoding='ascii')
shutil.copyfile(D / 'build.tcl', W / 'build.tcl')
tool = Path('C:/FudanMicro/Procise')
env = os.environ.copy()
env.update(APP_DIR=str(tool), ICTIME_HOME=str(tool), FMSH_DB=str(tool / 'db'), TCL_LIBRARY=str(tool / 'tcl8.4'))
env['PATH'] = str(tool / 'dll') + ';' + env['PATH']
start = time.monotonic()
timed = False
with (D / 'stdout.log').open('wb') as stdout, (D / 'stderr.log').open('wb') as stderr:
    proc = subprocess.Popen([str(tool / 'bin/procise.exe'), 'build.tcl'], cwd=W, env=env,
                            stdout=stdout, stderr=stderr, creationflags=subprocess.CREATE_NO_WINDOW)
    dump(D / 'owned-process.json', {'pid': proc.pid, 'work': str(W), 'budget_seconds': 180})
    try:
        proc.wait(timeout=180)
    except subprocess.TimeoutExpired:
        timed = True
        cleanup = subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'], capture_output=True, timeout=20)
        (D / 'cleanup.log').write_bytes(cleanup.stdout + cleanup.stderr)
        proc.wait(timeout=20)
execution = {'exit': proc.poll(), 'seconds': time.monotonic() - start, 'timeout': timed,
             'budget_seconds': 180, 'deployed': False, 'rebooted': False}
dump(D / 'execution.json', execution)
assert proc.poll() == 0 and not timed and output.is_file(), execution
new = output.read_bytes()
shutil.copyfile(output, D / output.name)
offset = rollback['BOOT_PL_offset_bytes']
length = rollback['BOOT_PL_bytes']
end = offset + length
assert len(new) == len(original) and end <= len(new), 'BOOT partition size changed; review required'
swapped = b''.join(new[i:i+4][::-1] for i in range(offset, end, 4))
result = {
    'bytes': len(new), 'sha256': sha(new), 'original_BOOT_sha256': sha(original),
    'PL_offset': offset, 'PL_bytes': length,
    'all_bytes_outside_PL_identical': original[:offset] == new[:offset] and original[end:] == new[end:],
    'PL_payload_matches_candidate_after_word_swap': swapped[:len(payload)] == payload,
    'padding_identical': new[offset+len(payload):end] == original[offset+len(payload):end],
    'candidate_bit_sha256': expected['sha256'], 'candidate_payload_sha256': sha(payload),
    'differing_PL_bytes': sum(a != b for a, b in zip(original[offset:end], new[offset:end])),
    'scope': 'offline candidate only; no deployment, boot configuration change, reboot or board acceptance',
}
dump(D / 'review.json', result)
shutil.copyfile(Path(__file__), D / Path(__file__).name)
print(json.dumps(result, ensure_ascii=False, indent=2))
assert result['all_bytes_outside_PL_identical'], 'Unexpected non-PL difference; stop'
assert result['PL_payload_matches_candidate_after_word_swap'] and result['padding_identical']
assert result['differing_PL_bytes'] > 0
