"""Offline Procise ICAP patch and BOOT packaging; never access the board."""
import hashlib
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

R = Path(__file__).resolve().parents[3]
E = R / 'tools/pose-v1/evidence/hdmi-boot-witness-20261019-r23'
W = R / '.local/hdmi-boot-witness-20261019-r23'
P = Path('C:/FudanMicro/Procise')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def procise(name, body, cwd):
    script = E / (name + '.tcl')
    script.write_text('if {[catch {\n' + body + '\n} result]} '
                      '{puts "OFFLINE_FAILED $result";exit 1}\nexit\n', encoding='ascii')
    env = os.environ.copy()
    env.update(APP_DIR=str(P), ICTIME_HOME=str(P), FMSH_DB=str(P / 'db'),
               PROCISE_DIR=str(P), TCL_LIBRARY=str(P / 'tcl8.4'))
    env['PATH'] = str(P / 'dll') + ';' + str(P / 'bin') + ';' + env['PATH']
    start = time.monotonic()
    with (E / (name + '.stdout.log')).open('xb') as out, (E / (name + '.stderr.log')).open('xb') as err:
        command = [str(P / 'bin/procise.exe'), str(script)]
        child = subprocess.Popen(command, cwd=cwd, env=env, stdout=out, stderr=err,
                                 creationflags=subprocess.CREATE_NO_WINDOW)
        record = dict(command=command, pid=child.pid, started_unix=time.time(), automatic_kill=False)
        (E / (name + '-process.json')).write_text(json.dumps(record, indent=2))
        while child.poll() is None:
            try:
                child.wait(timeout=30)
            except subprocess.TimeoutExpired:
                print(json.dumps(dict(stage=name, pid=child.pid, elapsed=time.monotonic() - start)), flush=True)
    record.update(exit_code=child.returncode, seconds=time.monotonic() - start)
    (E / (name + '-execution.json')).write_text(json.dumps(record, indent=2))
    if child.returncode:
        raise RuntimeError(f'{name}: native Procise exit {child.returncode}; preserve raw logs')


def main():
    global E, W
    cli = argparse.ArgumentParser()
    cli.add_argument('--evidence', type=Path, default=E)
    cli.add_argument('--work', type=Path, default=W)
    cli.add_argument('--raw-bit', type=Path)
    cli.add_argument('--bit-stage', default='bit2')
    cli.add_argument('--boot-name', default='BOOT-boot-witness-r23.bin')
    cli.add_argument('--repository-root', type=Path, default=R)
    args = cli.parse_args()
    assets = args.repository_root.resolve()
    E, W = args.evidence.resolve(), args.work.resolve()
    qualification = json.loads((E / 'qualification.json').read_text())
    if qualification.get('bit_generation_prerequisite_pass') is not True:
        raise RuntimeError('Physical timing/CDC/DRC prerequisite has not passed')
    if json.loads((E / (args.bit_stage + '-execution.json')).read_text())['exit_code']:
        raise RuntimeError('Native bit generation did not complete')
    parser_spec = importlib.util.spec_from_file_location('bit_parser', R / 'tools/pose-v1/inspect_selected_boot.py')
    parser = importlib.util.module_from_spec(parser_spec)
    parser_spec.loader.exec_module(parser)
    output = W / 'boot-package'
    output.mkdir(exist_ok=False)
    raw = (args.raw_bit.resolve() if args.raw_bit else
           W / 'reference/fpai_demo_vivado.runs/bit_boot_r23/ai7030_edif_top.bit')
    patched = output / 'ai7030_top_disable_icap.bit'
    procise('icap', 'set_device JFMQL30TAI676H\nincrement_bit_cfg_v3 {' + raw.as_posix()
            + '} {' + patched.as_posix() + '} -disable_icap', output)
    raw_bytes = raw.read_bytes()
    bit = patched.read_bytes()
    payload, header = parser.bit_payload(bit)
    if len(payload) != 5980460:
        raise RuntimeError('PL payload does not fit the original BOOT partition')
    control = assets / '.local/hdmi-board-reference-20261016-r1/boot-control-utf8-r2'
    original = (assets / 'tools/pose-v1/evidence/hdmi-reset-calibration-20261018-r20/BOOT-original.readback.bin').read_bytes()
    if sha(original) != 'ff350477e624c50d2f8180fb4b9130ec7688fbc7ca553412ed7c3dd2a68b31ef':
        raise RuntimeError('Original BOOT identity differs')
    if (control / 'BOOT-control.bin').read_bytes() != original:
        raise RuntimeError('Previously validated BOOT control differs from original')
    inputs = {}
    for name in ('FSBL251210_ddr400_demo.out', 'bl31.elf', 'u-boot'):
        source = control / name
        data = source.read_bytes()
        shutil.copyfile(source, output / name)
        inputs[name] = dict(bytes=len(data), sha256=sha(data), source=str(source))
    bif = (control / 'control.bif').read_text().replace(control.as_posix(), output.as_posix())
    (output / 'candidate.bif').write_text(bif, encoding='ascii')
    if Path(args.boot_name).name != args.boot_name:
        raise ValueError('--boot-name must be a filename')
    boot = output / args.boot_name
    procise('boot-package', 'create_boot_image {' + (output / 'candidate.bif').as_posix()
            + '} {' + boot.as_posix() + '} -fmql', output)
    new = boot.read_bytes()
    offset, end = 186816, 186816 + 5980464
    swapped = b''.join(new[i:i + 4][::-1] for i in range(offset, end, 4))
    review = dict(bytes=len(new), sha256=sha(new), original_sha256=sha(original),
                  all_bytes_outside_PL_identical=len(new) == len(original)
                  and new[:offset] == original[:offset] and new[end:] == original[end:],
                  PL_offset=offset, PL_bytes=end - offset,
                  PL_payload_matches_candidate_after_word_swap=swapped[:len(payload)] == payload,
                  padding_identical=new[offset + len(payload):end] == original[offset + len(payload):end],
                  differing_PL_bytes=sum(a != b for a, b in zip(original[offset:end], new[offset:end])),
                  raw_bit=dict(path=str(raw), bytes=len(raw_bytes), sha256=sha(raw_bytes)),
                  ICAP_bit=dict(path=str(patched), bytes=len(bit), sha256=sha(bit), header=header),
                  payload=dict(bytes=len(payload), sha256=sha(payload)), firmware_inputs=inputs,
                  BOOT_path=str(boot), deployed=False, rebooted=False)
    (E / 'package-review.json').write_text(json.dumps(review, indent=2))
    if not (review['all_bytes_outside_PL_identical'] and review['PL_payload_matches_candidate_after_word_swap']
            and review['padding_identical'] and review['differing_PL_bytes'] > 0):
        raise RuntimeError('BOOT partition/word-swap gate failed; no deployment')
    print(json.dumps(review, indent=2), flush=True)


if __name__ == '__main__':
    main()
