"""R6-only formal report adapter; no EDA/device access or new waiver."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json

ROOT=Path(__file__).resolve().parents[3]
E=ROOT/'tools/pose-v1/evidence/hdmi-live-20261017-r3'
BASE=Path(__file__).with_name('review_ai_read_route.py')
BASE_SHA='48a1506553804c2b033bbe41d527eca41a9f8b610bed6b32999f6cc89e60053c'
CONTRACT=Path(__file__).with_name('ai_read_postroute_contract.py')
CONTRACT_SHA='37f1f50aa55f866d59260a350b25dc0cf9de0e423597bbeb9d65b2e96853fb6b'
CHANGES=[
 (37,21,'read-v3r5-reports','read-v3r6-reports'),
 (38,29,'review.json','common-routed-review.json'),
 (39,18,'read-v3r5-bootstrap','read-v3r6-bootstrap'),
 (39,41,'read-v3r5-route','read-v3r6-route'),
 (39,60,'read-v3r5-reports','read-v3r6-reports'),
 (53,32,'read-v3r5-route/routed-checkpoint.json','read-v3r6-route/routed-checkpoint.json'),
 (54,30,'fpai_demo_vivado.runs/route_read_v3r5/ai7030_edif_top_routed.dcp','fpai_demo_vivado.runs/route_read_v3r6/ai7030_edif_top_routed.dcp'),
 (91,26,'read-v3r5-','read-v3r6-'),
 (108,25,'fpai_demo_vivado.runs/route_read_v3r5','fpai_demo_vivado.runs/route_read_v3r6'),
 (203,30,'route_read_v3r5','route_read_v3r6'),
 (224,17,'review.json','common-routed-review.json')]


def contract():
    actual=hashlib.sha256(CONTRACT.read_bytes()).hexdigest()
    if actual!=CONTRACT_SHA:raise ValueError('Frozen r6 public contract source changed')
    spec=importlib.util.spec_from_file_location('read_postroute_report_public_contract',CONTRACT)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check-only',action='store_true')
    args=parser.parse_args();helper=contract()
    common,adaptation,base_raw,adapted_raw=helper.adapt_frozen(BASE,BASE_SHA,CHANGES,Path(__file__))
    if args.check_only:
        print(json.dumps({'check_only':True,'EDA_started':False,'adaptation':adaptation},indent=2));return
    directory=E/'read-v3r6-reports'
    helper.need(directory.is_dir() and not (directory/'review.json').exists() and
                not (directory/'common-routed-review.json').exists(),'Fresh actual r6 reports required')
    optimization=helper.verify_optimizer()
    for name,raw in (('actual-r6-review-adapter.py',Path(__file__).read_bytes()),
                     ('base-r5-report-algorithms.py',base_raw),('adapted-report-algorithms.py',adapted_raw)):
        with (directory/name).open('xb') as stream:stream.write(raw)
    helper.save_new(directory/'report-algorithm-adapter.json',adaptation)
    # This unchanged formal algorithm must complete every original gate before
    # it can create the preserved common result. The base __file__ stays true.
    common.main()
    common_path=directory/'common-routed-review.json';review=helper.load(common_path)
    helper.need(review.get('bit_generation_prerequisite_pass') is True and
                review.get('candidate_run')=='route_read_v3r6' and review.get('managed_run') is False,
                'All original formal routed gates must pass')
    review.update(postroute_optimization=optimization,algorithm_adapter=adaptation,
                  actual_adapter_sha256=helper.sha(Path(__file__)),
                  common_routed_review_sha256=helper.sha(common_path),
                  postroute_contract_sha256=CONTRACT_SHA)
    helper.save_new(directory/'review.json',review)
    print(json.dumps({'bit_generation_prerequisite_pass':True,'candidate_run':'route_read_v3r6',
                      'managed_run':False,'new_timing_or_DRC_waiver':False},indent=2))


if __name__=='__main__':main()
