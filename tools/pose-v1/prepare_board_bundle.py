"""Bundle fixed inputs/references and the unchanged ARM checker, with hashes."""
import argparse
import hashlib
import json
import tarfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixtures', required=True, type=Path)
    parser.add_argument('--executable', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Preserve prior evidence; select a new archive path')
    manifest = json.loads((args.fixtures / 'manifest.json').read_text())
    paths = [args.executable, Path(__file__).with_name('numeric_metrics.py'), args.fixtures / 'manifest.json']
    for item in manifest['cases']:
        for suffix, key in (('.csi', 'input_sha256'), ('.reference.f32', 'reference_sha256')):
            path = args.fixtures / (item['stem'] + suffix)
            if hashlib.sha256(path.read_bytes()).hexdigest() != item[key]:
                raise ValueError('Fixture hash mismatch')
            paths.append(path)
    paths.extend(sorted(args.fixtures.glob('invalid_*.csi')))
    with tarfile.open(args.output, 'x:gz') as bundle:
        for path in paths:
            bundle.add(path, arcname=path.name, recursive=False)
    print(json.dumps({'archive': str(args.output), 'bytes': args.output.stat().st_size,
                      'sha256': hashlib.sha256(args.output.read_bytes()).hexdigest(),
                      'executable_sha256': hashlib.sha256(args.executable.read_bytes()).hexdigest(),
                      'manifest_sha256': hashlib.sha256((args.fixtures / 'manifest.json').read_bytes()).hexdigest(),
                      'numeric_metrics_sha256': hashlib.sha256(Path(__file__).with_name('numeric_metrics.py').read_bytes()).hexdigest(),
                      'members': len(paths), 'cases': len(manifest['cases'])}))


if __name__ == '__main__':
    main()
