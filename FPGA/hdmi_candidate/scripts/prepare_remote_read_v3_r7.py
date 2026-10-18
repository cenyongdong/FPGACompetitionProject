"""Isolated r7 adapter for the frozen finite source generator; default offline."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
HOST = Path(__file__).with_name('controlled_read_v3_r7.py')
HOST_SHA256 = '47c0666f168628f60dd104c6e786962ae5a48cb2926679aa0f3b6a6b81f87aa7'
raw = HOST.read_bytes()
if hashlib.sha256(raw).hexdigest() != HOST_SHA256:
    raise ValueError('Frozen r7 Host adapter source changed or is not yet bound')
spec = importlib.util.spec_from_file_location('r7_generator_Host_contract', HOST)
host = importlib.util.module_from_spec(spec)
host.r7_loaded_source_SHA256 = HOST_SHA256
exec(compile(raw, str(HOST), 'exec'), vars(host))
backend = host.adapter('generator')


def __getattr__(name):
    return getattr(backend, name)


def main():
    if sys.argv[1:] == ['--source-check']:
        print(json.dumps(host.source_preparation('generator'), indent=2))
        return 0
    return backend.main()


if __name__ == '__main__':
    raise SystemExit(main())
