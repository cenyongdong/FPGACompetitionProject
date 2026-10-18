"""Final read-only artifact checks plus new documentation revision evidence."""
import difflib
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def sha(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def main():
    manifest = json.loads((HERE / 'manifest.json').read_text(encoding='utf-8'))
    checked = []
    for record in manifest['artifacts'] + manifest['scripts']:
        path = ROOT / record['path']
        assert sha(path) == record['sha256'], path
        if 'bytes' in record:
            assert path.stat().st_size == record['bytes'], path
        checked.append(record['path'])
    assert json.loads((HERE / 'module-verification.json').read_text())['passed']
    assert json.loads((HERE / 'upstream-reference.json').read_text())['passed']
    assert json.loads((HERE / 'loopback-result.json').read_text())['passed']
    assert json.loads((HERE / 'parameter-verification.json').read_text())['passed']
    assert 'OFFLINE_BUILD_COMPLETE=1' in (HERE / 'logs/firmware-build-r8.log').read_text()
    assert 'Ran 14 tests' in (HERE / 'logs/host-tests-r3.log').read_text()
    native = (HERE / 'firmware-native-log/linker.err').read_text().splitlines()
    assert len(native) == 706 and all(': Removing unused section ' in line for line in native)
    assert (HERE / 'firmware-native-log/error.log').read_text().strip() == \
        'cat: gen/nexmon.pre: No such file or directory'
    assert 'nexmon-' not in (HERE / 'containers-after.txt').read_text()
    before = json.loads((HERE / 'documents/before.json').read_text(encoding='utf-8-sig'))
    revisions = []
    docs = [ROOT / 'tools/nexmon/README.md', ROOT / 'tools/nexmon/DEPLOYMENT-PLAN.md',
            HERE / 'REPORT.md']
    for record in before:
        current = ROOT / record['path']
        snapshot = HERE / 'documents' / (current.name + '.before')
        assert sha(snapshot) == record['before_sha256'], snapshot
        old, new = snapshot.read_text(encoding='utf-8'), current.read_text(encoding='utf-8')
        diff = ''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                         fromfile=record['path'] + ':before', tofile=record['path'] + ':after'))
        (HERE / 'documents' / (current.name + '.diff')).write_text(diff, encoding='utf-8')
        revisions.append(dict(path=record['path'], before_sha256=sha(snapshot),
                              after_sha256=sha(current), changed=old != new))
        docs.append(current)
    (HERE / 'documents/revisions.json').write_text(json.dumps(revisions, indent=2))
    links = []
    for doc in docs:
        for target in re.findall(r'\]\(([^)]+)\)', doc.read_text(encoding='utf-8')):
            if re.match(r'^(https?://|codex:)', target):
                continue
            target = target.split('#')[0].strip('<>')
            if not target:
                continue
            # Existing root indexes contain historical D:/ absolute links.
            resolved = Path(target) if re.match(r'^[A-Za-z]:[/\\]', target) else doc.parent / target
            # Audit only new Nexmon references and all links in the new documents.
            if doc in docs[:3] or 'nexmon' in target.lower():
                assert resolved.exists(), (doc, target)
                links.append(str(resolved))
    result = dict(passed=True, hardware_test=False, checked_hashes=len(checked),
                  checked_links=len(links), revised_documents=len(revisions),
                  linker_messages=len(native), task_containers_running=0,
                  limits='Offline preparation only; all router phases pending arrival')
    (HERE / 'verification.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result))


if __name__ == '__main__':
    main()
