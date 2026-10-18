"""Pure final-r6 review/bit release binding. No EDA or board operations."""
from pathlib import Path
import hashlib
import importlib.util
import json
import re

ROOT=Path(__file__).resolve().parents[3]
E=ROOT/'tools/pose-v1/evidence/hdmi-live-20261017-r3'
REF=ROOT/'.local/hdmi-live-20261017-r3/reference'
REVIEWER=Path(__file__).with_name('review_ai_read_postroute.py')
REVIEWER_SHA='d989800af0516b8b67fa21877bf776b41229e5828fd69f1a35ff71dc090e235c'
CONTRACT=Path(__file__).with_name('ai_read_postroute_contract.py')
CONTRACT_SHA='37f1f50aa55f866d59260a350b25dc0cf9de0e423597bbeb9d65b2e96853fb6b'
BASE_SHA='48a1506553804c2b033bbe41d527eca41a9f8b610bed6b32999f6cc89e60053c'


def need(okay,message):
    if not okay:raise ValueError(message)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def same_json(left,right):
    return json.dumps(left,sort_keys=True,allow_nan=False)==json.dumps(right,sort_keys=True,allow_nan=False)


def modules():
    need(sha(REVIEWER)==REVIEWER_SHA and sha(CONTRACT)==CONTRACT_SHA,'Frozen r6 release reviewer/contract changed')
    spec=importlib.util.spec_from_file_location('bit_r6_formal_review_adapter',REVIEWER)
    reviewer=importlib.util.module_from_spec(spec);spec.loader.exec_module(reviewer)
    return reviewer,reviewer.contract()


def verify_bit_release(identity,bit_input,evidence=None):
    evidence={} if evidence is None else evidence
    actual=identity.get('r6_routed_release');other=bit_input.get('r6_routed_release')
    need(isinstance(actual,dict) and same_json(actual,other),'Bit input/identity complete r6 release differs')
    reviewer,contract=modules()
    formal_path=E/'read-v3r6-reports/review.json'
    common_path=formal_path.with_name('common-routed-review.json')
    formal=load(formal_path);common=load(common_path)
    need(formal.get('bit_generation_prerequisite_pass') is True and common.get('bit_generation_prerequisite_pass') is True and
         formal.get('candidate_run')==common.get('candidate_run')=='route_read_v3r6' and
         formal.get('managed_run') is False and common.get('managed_run') is False and
         formal.get('new_timing_or_DRC_waiver') is False and
         formal.get('review_driver_SHA256')==common.get('review_driver_SHA256')==BASE_SHA and
         formal.get('actual_adapter_sha256')==REVIEWER_SHA and
         formal.get('postroute_contract_sha256')==CONTRACT_SHA and
         formal.get('common_routed_review_sha256')==sha(common_path),
         'All original formal r6 timing/DRC/algorithm gates required')
    _,adaptation,_,_=contract.adapt_frozen(reviewer.BASE,reviewer.BASE_SHA,reviewer.CHANGES,REVIEWER)
    optimization=contract.verify_optimizer()
    need(same_json(formal.get('algorithm_adapter'),adaptation) and
         same_json(formal.get('postroute_optimization'),optimization),
         'Formal r6 inverse-AST/complete raw optimization chain differs')
    drc=REF/'fpai_demo_vivado.runs/route_read_v3r6/ai7030_edif_top_drc_routed.rpt'
    reopened=E/'read-v3r6-reports/DRC-reopened-default-profile.rpt'
    raw=drc.read_text();default=reopened.read_text()
    errors=re.findall(r'^(\S+#\d+) Error$',raw,re.MULTILINE)
    disabled=re.findall(r'^The following rules are disabled: ([^\r\n]+)',raw,re.MULTILINE)
    default_errors=re.findall(r'^(\S+#\d+) Error$',default,re.MULTILINE)
    need(not errors and disabled==['REQP-44, REQP-46, REQP-52, REQP-56'] and
         default_errors==['REQP-52#1','REQP-56#1'] and
         formal.get('factory_DRC_profile_errors')==0 and
         formal.get('reopened_default_profile_errors_retained')==default_errors,
         'Actual factory/default DRC profile differs from formal release')
    profile={'routed_report_path':str(drc),'routed_report_SHA256':sha(drc),
             'disabled_rules':['REQP-44','REQP-46','REQP-52','REQP-56'],'error_count':0,
             'default_reopened_report_path':str(reopened),'default_reopened_report_SHA256':sha(reopened),
             'default_errors':default_errors}
    expected={'formal_review_path':str(formal_path),'formal_review_SHA256':sha(formal_path),
              'common_review_path':str(common_path),'common_review_SHA256':sha(common_path),
              'adapter_path':str(REVIEWER),'adapter_SHA256':REVIEWER_SHA,
              'contract_path':str(CONTRACT),'contract_SHA256':CONTRACT_SHA,
              'postroute_optimization':optimization,'algorithm_adapter':adaptation,
              'factory_DRC_profile':profile}
    need(same_json(actual,expected),'Complete real r6 bit release/profile object differs or has unrecognized fields')
    for path in (formal_path,common_path,REVIEWER,CONTRACT,reviewer.BASE,drc,reopened,Path(__file__)):
        evidence[str(path.resolve())]=sha(path)
    evidence.update(optimization['actual_evidence_sha256'])
    return expected
