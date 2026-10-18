"""Prepare an independent r7 reference; this program never starts EDA or a device.

The old 937-file ledger and 41 installed files are verified before and after.
Only 25 cached-control path migrations, one reader RTL and Project.Path change.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import time
import xml.etree.ElementTree as ET

R = Path(__file__).resolve().parents[3]
OLD = R / '.local/hdmi-live-20261017-r3/reference'
W = R / '.local/hdmi-live-20261017-r7'
REF = W / 'reference'
E = R / 'tools/pose-v1/evidence/hdmi-live-20261017-r7'
E3 = R / 'tools/pose-v1/evidence/hdmi-live-20261017-r3'
GATE = E3 / 'read-v3r3-constraints-r3/review.json'
INSTALLED = R / 'tools/pose-v1/evidence/hdmi-live-20261017-r2/toolchain-identity-review.json'
TOOL = Path('D:/vivado18.3/Vivado/2018.3')
MANAGED = E3 / 'managed-PS-observer-r2/review.json'
CANDIDATE_DIR = E3 / 'HDMI-received-idle-candidate-r1'
CANDIDATE = CANDIDATE_DIR / 'canonical-name-only/hdmi_axi_read.v'
READER = 'rtl/hdmi_candidate/hdmi_axi_read.v'
OLD_READER_SHA = '4608af5a4701aa18cdd1513966aae3301909883dc94ea43454bcbc0421f00e17'
NEW_READER_SHA = '05e3f0c32dfa2c328008f909a8ab6b804e40d135461d1369ed2c8d591ae60b93'


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def verify_map(base, values):
    actual = {}
    for relative, expected in values.items():
        path = base / relative
        require(path.is_file() and not path.is_symlink()
                and not getattr(path.lstat(), 'st_file_attributes', 0) & 0x400,
                'Missing/nonordinary input: ' + str(path))
        actual[relative] = sha(path)
        require(actual[relative] == expected, 'Identity mismatch: ' + str(path))
    return actual


def root_edits(raw, old, new):
    """ASCII byte edits; no decoding/reencoding of the enclosing file."""
    pattern = re.compile(re.escape(old.encode('ascii')) + rb'(?=[/\\]|$)', re.I)
    edits = [{'start': m.start(), 'end': m.end(), 'old': m.group().decode('ascii'),
              'new': new} for m in pattern.finditer(raw)]
    changed = raw
    for item in reversed(edits):
        changed = changed[:item['start']] + item['new'].encode('ascii') + changed[item['end']:]
    # Reverse by forward positions plus the accumulated length difference.
    inverse = changed
    for item in edits:
        begin = item['start']
        replacement = item['new'].encode('ascii')
        require(inverse[begin:begin + len(replacement)] == replacement, 'Inverse span mismatch')
        inverse = inverse[:begin] + item['old'].encode('ascii') + inverse[begin + len(replacement):]
        # Earlier reverse edits restore the original coordinate system.
    require(inverse == raw, 'Path migration is not exactly reversible')
    return changed, edits


def reject_reparse_tree(base):
    resolved = base.resolve()
    require(not base.is_symlink() and not getattr(base.lstat(), 'st_file_attributes', 0) & 0x400,
            'Root reparse point rejected')
    count = 0
    for directory, names, files in os.walk(base, topdown=True, followlinks=False):
        for name in names + files:
            path = Path(directory) / name
            require(not path.is_symlink()
                    and not getattr(path.lstat(), 'st_file_attributes', 0) & 0x400,
                    'Source reparse point rejected before traversal: ' + str(path))
            require(path.resolve().is_relative_to(resolved), 'Source resolved outside root: ' + str(path))
            count += 1
    return count


def preflight():
    reject_reparse_tree(OLD)
    source = load(GATE)['source_sha256']
    require(len(source) == 937, 'Expected fixed 937 source ledger')
    installed = load(INSTALLED)
    require(installed['matching'] is True and installed['checked_files'] == 41
            and len(installed['actual']) == 41, 'Installed ledger invalid')
    before = verify_map(OLD, source)
    libs = verify_map(TOOL, installed['actual'])
    require(source[READER] == OLD_READER_SHA and sha(CANDIDATE) == NEW_READER_SHA,
            'Reader identities differ')
    miter = load(CANDIDATE_DIR / 'run-r1/result.json')
    require(miter['passed'] is True and miter['strict_output_bits'] == 116
            and miter['cases'] == 24 and miter['cycles'] == 5773
            and miter['comparisons'] == 11378, 'Actual finite miter receipt invalid')
    proof = load(CANDIDATE_DIR / 'canonical-name-proof.json')
    tested = CANDIDATE_DIR / 'rtl/hdmi_axi_read_idle_candidate.v'
    require(proof['all_other_bytes_equal_to_tested_candidate'] is True
            and proof['SHA256'] == NEW_READER_SHA
            and sha(tested) == proof['tested_candidate_SHA256'], 'Canonical name proof invalid')
    require(tested.read_bytes().count(b'module hdmi_axi_read_idle_candidate') == 1
            and tested.read_bytes().replace(b'module hdmi_axi_read_idle_candidate',
                                           b'module hdmi_axi_read', 1) == CANDIDATE.read_bytes(),
            'Canonical file differs beyond one module-name inverse')
    migrations = []
    for relative in source:
        raw = (OLD / relative).read_bytes()
        changed, edits = root_edits(raw, OLD.as_posix(), REF.as_posix())
        if edits:
            require(changed != raw, 'No-op path migration')
            migrations.append(relative)
    expected = {'procise_run_disable_icap.tcl'} | {
        p.relative_to(OLD).as_posix() for p in (OLD / 'fpai_demo_vivado.runs').glob('*_synth_1/*.tcl')
        if p.name == p.parent.name.removesuffix('_synth_1') + '.tcl'}
    require(len(expected) == 25 and set(migrations) == expected, 'Exact 25-file path whitelist changed')
    xpr = (OLD / 'fpai_demo_vivado.xpr').read_bytes()
    tree = ET.fromstring(xpr)
    require(tree.attrib['Path'] == (OLD / 'fpai_demo_vivado.xpr').as_posix(), 'Old Project.Path differs')
    require(all(p.get('Path', '').startswith(('$PPRDIR/', '$PSRCDIR/')) for p in tree.iter('File')),
            'XPR has an unexpected absolute file source')
    require(len(list(tree.iter('File'))) == 115, 'XPR source registration count differs')
    ooc = [n.get('Id') for n in tree.iter('Run') if n.get('Id', '').endswith('_synth_1')]
    require(len(ooc) == 24, 'OOC run inventory differs')
    return source, libs, migrations, xpr, ooc, before


def prepare():
    started = time.monotonic()
    require(not W.exists() and not E.exists(), 'Fresh W7/E7 required; partial failure must be retained')
    source, libs, paths, xpr, ooc, before = preflight()
    W.mkdir(); E.mkdir(); out = E / 'preparation'; out.mkdir()
    (out / 'actual-preparer.py').write_bytes(Path(__file__).read_bytes())
    (out / 'fpai_demo_vivado.xpr.before').write_bytes(xpr)
    save(out / 'original-source-ledger.json', source)
    save(out / 'installed-ledger.json', libs)
    inventory = {}

    def copy_one(src, dst):
        require(time.monotonic() - started < 300, 'Copy budget expired; retain partial new tree')
        source_path = Path(src)
        destination = Path(dst)
        require(source_path.resolve().is_relative_to(OLD.resolve())
                and not source_path.is_symlink()
                and not getattr(source_path.lstat(), 'st_file_attributes', 0) & 0x400,
                'Source escaped/reparse point rejected')
        require(destination.parent.resolve().is_relative_to(REF.resolve()) and not destination.exists(),
                'Destination escaped/already exists')
        shutil.copy2(src, dst)
        require(destination.is_file() and not destination.is_symlink()
                and not getattr(destination.lstat(), 'st_file_attributes', 0) & 0x400
                and destination.stat().st_nlink == 1 and not os.path.samefile(source_path, destination),
                'Copied destination is not an independent ordinary file')
        first, second = sha(source_path), sha(Path(dst))
        require(first == second, 'Byte copy mismatch: ' + str(src))
        inventory[source_path.relative_to(OLD).as_posix()] = {
            'bytes': source_path.stat().st_size, 'SHA256': first}
        return dst

    def ignore(directory, names):
        current = Path(directory)
        require(current.resolve().is_relative_to(OLD.resolve()), 'Copy traversal escaped original root')
        for name in names:
            path = current / name
            require(not path.is_symlink() and not getattr(path.lstat(), 'st_file_attributes', 0) & 0x400,
                    'Reparse child rejected before copy traversal: ' + str(path))
        omitted = {'.Xil', '.git', '.jobs', 'fpai_demo_vivado.sim', 'fpai_demo_vivado.hw'}
        if Path(directory).name == 'fpai_demo_vivado.runs':
            omitted.update(n for n in names if n not in ooc)
        return [n for n in names if n in omitted]

    shutil.copytree(OLD, REF, copy_function=copy_one, ignore=ignore)
    verify_map(REF, source)
    save(out / 'copy-byte-identities.json', inventory)
    migrations = {}
    snapshots = out / 'changed-files'; snapshots.mkdir()
    for relative in paths:
        path = REF / relative; raw = path.read_bytes()
        changed, edits = root_edits(raw, OLD.as_posix(), REF.as_posix())
        index = len(migrations)
        (snapshots / f'{index:02d}.before').write_bytes(raw)
        (snapshots / f'{index:02d}.after').write_bytes(changed)
        path.write_bytes(changed)
        migrations[relative] = {'before_SHA256': source[relative], 'after_SHA256': sha(path),
                                'edits': edits, 'inverse_byte_exact': True,
                                'snapshot_before': str(snapshots / f'{index:02d}.before'),
                                'snapshot_after': str(snapshots / f'{index:02d}.after')}
    old_path = (OLD / 'fpai_demo_vivado.xpr').as_posix().encode('ascii')
    new_path = (REF / 'fpai_demo_vivado.xpr').as_posix().encode('ascii')
    attribute = b'Path="' + old_path + b'"'
    require(xpr.count(attribute) == 1, 'Project.Path replacement not unique')
    after_xpr = xpr.replace(attribute, b'Path="' + new_path + b'"', 1)
    require(after_xpr.replace(b'Path="' + new_path + b'"', attribute, 1) == xpr,
            'XPR exact inverse failed')
    (REF / 'fpai_demo_vivado.xpr').write_bytes(after_xpr)
    (out / 'fpai_demo_vivado.xpr.after').write_bytes(after_xpr)
    (snapshots / 'reader.before').write_bytes((REF / READER).read_bytes())
    (REF / READER).write_bytes(CANDIDATE.read_bytes())
    (snapshots / 'reader.after').write_bytes((REF / READER).read_bytes())
    updated = {name: sha(REF / name) for name in source}
    changed = {name for name in source if source[name] != updated[name]}
    require(changed == set(paths) | {READER}, 'Unexpected protected-source difference')
    old_after = verify_map(OLD, source); installed_after = verify_map(TOOL, libs)
    require((OLD / 'fpai_demo_vivado.xpr').read_bytes() == xpr, 'Original XPR changed during preparation')
    require(sha(REF / READER) == NEW_READER_SHA, 'Final canonical reader differs')
    save(out / 'source-ledger.json', updated)
    functional = {'path': READER, 'before_SHA256': OLD_READER_SHA, 'after_SHA256': NEW_READER_SHA,
                  'canonical_path': str(CANDIDATE), 'canonical_SHA256': sha(CANDIDATE),
                  'canonical_name_proof_path': str(CANDIDATE_DIR / 'canonical-name-proof.json'),
                  'canonical_name_proof_SHA256': sha(CANDIDATE_DIR / 'canonical-name-proof.json'),
                  'miter_result_path': str(CANDIDATE_DIR / 'run-r1/result.json'),
                  'miter_result_SHA256': sha(CANDIDATE_DIR / 'run-r1/result.json'),
                  'production_repository_or_old_REF_modified': False}
    result = {'passed': True, 'schema': 'hdmi-reader-idle-r7-preparation-v1',
              'old_reference': str(OLD), 'new_reference': str(REF), 'source_count': len(source),
              'source_sha256': updated, 'original_source_sha256': source,
              'original_source_ledger_path': str(out / 'original-source-ledger.json'),
              'source_ledger_path': str(out / 'source-ledger.json'),
              'source_gate_path': str(GATE), 'source_gate_SHA256': sha(GATE),
              'path_migrations': migrations, 'functional_change': functional,
              'installed_sha256': libs, 'installed_identity_ledger_path': str(INSTALLED),
              'installed_identity_ledger_SHA256': sha(INSTALLED),
              'managed_PS_receipt_path': str(MANAGED), 'managed_PS_receipt_SHA256': sha(MANAGED),
              'xpr': {'before_SHA256': hashlib.sha256(xpr).hexdigest(),
                      'after_SHA256': hashlib.sha256(after_xpr).hexdigest(),
                      'only_Project_Path_changed': True, 'inverse_byte_exact': True,
                      'old': old_path.decode(), 'new': new_path.decode(), 'substitution_count': 1},
              'OOC_cached_run_names': ooc, 'OOC_cached_scripts_must_not_execute': True,
              'old_source_before': before, 'old_source_after': old_after,
              'installed_before': libs, 'installed_after': installed_after,
              'copied_files': len(inventory), 'copied_bytes': sum(v['bytes'] for v in inventory.values()),
              'preparer_SHA256': sha(Path(__file__)), 'seconds': time.monotonic() - started,
              'EDA_executed': False, 'board_executed': False, 'BOOT_or_reboot_authorization': False}
    save(out / 'review.json', result)
    print(json.dumps({k: result[k] for k in ['passed', 'source_count', 'copied_files', 'copied_bytes',
                                           'seconds', 'EDA_executed', 'board_executed']}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true', help='Create fresh local directories; never starts EDA')
    args = parser.parse_args()
    if args.prepare:
        prepare()
    else:
        source, libs, paths, _, ooc, _ = preflight()
        print(json.dumps({'ready': True, 'read_only': True, 'source_count': len(source),
                          'installed_count': len(libs), 'path_migrations': len(paths), 'OOC_count': len(ooc),
                          'new_workspace_exists': W.exists(), 'new_evidence_exists': E.exists(),
                          'EDA_executed': False, 'board_executed': False}))


if __name__ == '__main__':
    main()
