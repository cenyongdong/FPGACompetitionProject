"""本次检查包装：复用既有检查器，结果写入新目录，保留旧证据。"""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
PYTHON = Path(sys.executable)
TAG = '20261014-r1'


def main():
    files = []
    for base in ('software/core', 'software/demo'):
        for path in sorted((ROOT / base).rglob('*.py')):
            compile(path.read_bytes(), str(path), 'exec')
            files.append(path.relative_to(ROOT).as_posix())
    (EVIDENCE / 'python-syntax.json').write_text(json.dumps({
        'status': 'passed', 'files': files,
        'python': sys.version, 'imports_or_hardware_not_executed': True
    }, indent=2) + '\n', encoding='utf-8')

    spec = importlib.util.spec_from_file_location('core_check', ROOT / 'software/demo/verify_core.py')
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    original_save = checker.save

    def save_new(path, value):
        if path.parent == checker.EVIDENCE:
            path = EVIDENCE / path.name
        assert not path.exists() or path.name == 'steps.json'
        original_save(path, value)

    checker.save = save_new
    checker.native(TAG)
    command = [str(PYTHON), str(ROOT / 'software/demo/build.py'),
               '--tag', 'demo-core-check-' + TAG]
    result = subprocess.run(command, capture_output=True)
    (EVIDENCE / 'build.stdout.txt').write_bytes(result.stdout)
    (EVIDENCE / 'build.stderr.txt').write_bytes(result.stderr)
    (EVIDENCE / 'build-command.json').write_text(json.dumps({
        'argv': command, 'exit': result.returncode,
        'working_directory': str(ROOT)
    }, indent=2) + '\n', encoding='utf-8')
    print(result.stdout.decode(errors='replace'), flush=True)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors='replace'))


if __name__ == '__main__':
    main()
