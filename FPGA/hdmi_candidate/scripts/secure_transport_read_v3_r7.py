"""r7 public pin/askpass adapter; raw transport CLI is not an execution entry."""
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
spec = importlib.util.spec_from_file_location('r7_secure_Host_contract', HOST)
host = importlib.util.module_from_spec(spec)
host.r7_loaded_source_SHA256 = HOST_SHA256
exec(compile(raw, str(HOST), 'exec'), vars(host))
backend = host.adapter('secure_transport')


def __getattr__(name):
    return getattr(backend, name)


def main():
    if sys.argv[1:] in [[], ['inspect'], ['--source-check']]:
        print(json.dumps(host.source_preparation('secure_transport'), indent=2))
        return 0
    if len(sys.argv) > 1 and sys.argv[1] == 'askpass':
        return backend.main()
    raise ValueError('Direct r7 transport is closed; use the separately gated stage/startup entry')


if __name__ == '__main__':
    raise SystemExit(main())
