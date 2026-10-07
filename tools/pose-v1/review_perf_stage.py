"""Review the frozen r3 package; supply its omitted stdlib hashlib import.

The packaged reviewer, build and binary identities remain unchanged. This
entry point only supplies a Python standard-library binding; no data, hashes,
scope checks or timing calculations are substituted.
"""
import argparse
import hashlib
from pathlib import Path
import perf_gate

perf_gate.hashlib=hashlib

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage',choices=['host-check','e0','p1'],required=True)
    for k in ('package','build','results','output'):p.add_argument('--'+k,type=Path,required=True)
    perf_gate.review(p.parse_args())
