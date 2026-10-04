"""Diagnostic substitution only: quantify vector/scalar atan2 sensitivity.
Does not change production preprocessing or the original training file.
"""
import argparse
import json
import math
from pathlib import Path
import numpy as np
from validate_preprocess import training_processor, reference


def scalar_angle(z):
    values=np.asarray(z)
    return np.fromiter((math.atan2(float(v.imag),float(v.real)) for v in values.flat),
                       dtype=np.float64,count=values.size).reshape(values.shape)


class ScalarAngleDiagnostic:
    def angle(self,z):
        return scalar_angle(z)
    def __getattr__(self,name):
        return getattr(np,name)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--repo',required=True,type=Path)
    p.add_argument('--fixtures',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    args=p.parse_args()
    rows=[]
    for stem in ('case_04','case_05'):
        raw=(args.fixtures/(stem+'.csi')).read_bytes()
        pairs=np.frombuffer(raw,dtype='<f8',offset=32).reshape(3,3,30,20,2)
        z=np.empty((3,3,30,20),dtype=np.complex128)
        z.real=pairs[...,0];z.imag=pairs[...,1]
        original=training_processor(args.repo/'opera/datasets/wifi_pose.py')
        expected=reference(z,original)
        stored=np.fromfile(args.fixtures/(stem+'.reference.f32'),dtype='<f4').reshape(1,180,60)
        if not np.array_equal(expected.view(np.uint32),stored.view(np.uint32)):
            raise ValueError('Reloaded fixture differs from original reference')
        diagnostic=training_processor(args.repo/'opera/datasets/wifi_pose.py')
        diagnostic.CSI_sanitization.__func__.__globals__['np']=ScalarAngleDiagnostic()
        changed=reference(z,diagnostic)
        actual=np.fromfile(args.fixtures/(stem+'.host.f32'),dtype='<f4').reshape(1,180,60)
        rows.append({'case':stem,
            'raw_angle_numpy_vs_math_max_abs':float(np.max(np.abs(np.angle(z)-scalar_angle(z)))),
            'original_reference_vs_cpp_max_abs':float(np.max(np.abs(expected.astype(np.float64)-actual))),
            'diagnostic_scalar_angle_reference_vs_cpp_max_abs':float(np.max(np.abs(changed.astype(np.float64)-actual))),
            'diagnostic_scalar_angle_reference_vs_cpp_bitwise_equal':bool(np.array_equal(changed.view(np.uint32),actual.view(np.uint32)))})
    report={'scope':'offline diagnostic substitution; production/training algorithm unchanged',
            'cases':rows,'acceptance':'not approved; no tolerance or boundary-policy change'}
    args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(rows))


if __name__=='__main__':
    main()
