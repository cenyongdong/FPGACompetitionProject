"""R6-only offline package adapter. Default inspect; no deployment/reboot."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import sys

ROOT=Path(__file__).resolve().parents[3]
BASE=Path(__file__).with_name('package_ai_read_offline.py')
BASE_SHA='bf39a9e49a264d94b5033141560ac9c115c4b214faf104dac377a050e639ac3f'
CONTRACT=Path(__file__).with_name('ai_read_postroute_contract.py')
CONTRACT_SHA='37f1f50aa55f866d59260a350b25dc0cf9de0e423597bbeb9d65b2e96853fb6b'
PLANNER_SHA='7d170d0e800d5d9a9fe870628c65957d703f6b6fdd970ddbc28370b89a0a0154'
CHANGES=[
 (35,19,'2e6b57a9351caffa648251e89799bcaf02d412d42d77a224a041789a12a0b65a',PLANNER_SHA),
 (65,27,'read-v3r5-bit','read-v3r6-bit'),
 (182,38,'read-v3r5-reports/review.json','read-v3r6-reports/review.json'),
 (185,44,'route_read_v3r5','route_read_v3r6'),
 (205,42,'route_read_v3r5','route_read_v3r6'),
 (207,73,'read-v3r5-bit/bit-identity.json','read-v3r6-bit/bit-identity.json'),
 (279,22,'reference/fpai_demo_vivado.runs/route_read_v3r5/ai7030_edif_top.bit','reference/fpai_demo_vivado.runs/route_read_v3r6/ai7030_edif_top.bit'),
 (307,26,'route_read_v3r5','route_read_v3r6'),
 (308,9,'r5_bit_gate','r6_bit_gate'),
 (318,35,'route_read_v3r5','route_read_v3r6'),
 (363,31,'route_read_v3r5','route_read_v3r6'),
 (379,77,'route_read_v3r5','route_read_v3r6'),
 (488,13,'r5_bit_gate','r6_bit_gate')]


def contract():
    if hashlib.sha256(CONTRACT.read_bytes()).hexdigest()!=CONTRACT_SHA:
        raise ValueError('Frozen r6 package contract source changed')
    spec=importlib.util.spec_from_file_location('r6_offline_package_public_contract',CONTRACT)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def prepared():
    helper=contract()
    common,adaptation,base_raw,adapted_raw=helper.adapt_frozen(BASE,BASE_SHA,CHANGES,Path(__file__))
    base_stage=common.Stage
    class ArchivedR6Stage(base_stage):
        def __init__(self,mode):
            super().__init__(mode)
            for name,raw in (('actual-r6-packager-adapter.py',Path(__file__).read_bytes()),
                             ('base-r5-packager-algorithms.py',base_raw),('adapted-packager-algorithms.py',adapted_raw)):
                self.save(name,raw)
            helper.save_new(self.out/'package-algorithm-adapter.json',adaptation)
            self.read(BASE,BASE_SHA);self.read(CONTRACT,CONTRACT_SHA);self.read(Path(__file__))
        def gate(self):
            super().gate()
            evidence={};optimization=helper.verify_optimizer(evidence)
            for path,expected in evidence.items():self.read(Path(path),expected)
            self.bit_gate['postroute_optimization']=optimization
            self.bit_gate['algorithm_adapter']=adaptation
    common.execution_namespace['Stage']=ArchivedR6Stage
    adaptation['runtime_gate_extension']='archive real sources; freeze actual optimizer evidence before any Procise'
    return common,adaptation


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',nargs='?',choices=('inspect','icap','boot','bundle'),default='inspect')
    args=parser.parse_args();common,adaptation=prepared()
    if args.mode=='inspect':
        print(json.dumps({'inspect_only':True,'tools_started':False,'adaptation':adaptation},indent=2));return 0
    old=sys.argv;sys.argv=[str(BASE),args.mode]
    try:return common.main()
    finally:sys.argv=old


if __name__=='__main__':raise SystemExit(main())
