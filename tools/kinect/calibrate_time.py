"""Fit a clock transform from measured common-event anchors, not arrival times."""
import argparse
import csv
import json
from pathlib import Path
import numpy as np


def fit(rows, evidence):
    if len(rows)<3 or len({str(r['csi_session']) for r in rows})!=1:
        raise ValueError('At least three measured anchors from one CSI session are required')
    source=[int(r['source_ns']) for r in rows];ticks=[int(r['kinect_ticks_100ns']) for r in rows]
    uncertainty=np.asarray([float(r['uncertainty_ms']) for r in rows])
    if len(set(source))!=len(source) or not np.isfinite(uncertainty).all() or (uncertainty<0).any():
        raise ValueError('Invalid or duplicate anchor measurements')
    origin=source[0];tick_origin=ticks[0]
    x=np.asarray([s-origin for s in source],dtype=float);y=np.asarray([t-tick_origin for t in ticks],dtype=float)
    scale,intercept=np.linalg.lstsq(np.column_stack((x,np.ones_like(x))),y,rcond=None)[0]
    residual_ms=np.abs(y-(scale*x+intercept))/10000
    if not np.isfinite(scale) or scale<=0:raise ValueError('Clock fit is not monotonic')
    return dict(verified=True,evidence=str(evidence),input_source='live-csi',csi_session=str(rows[0]['csi_session']),
        label_time_reference='window_end',reference_source_ns=origin,
        reference_kinect_ticks_100ns=int(round(tick_origin+intercept)),ticks_per_source_ns=float(scale),
        valid_source_min_ns=min(source),valid_source_max_ns=max(source),
        max_error_ms=float(np.max(residual_ms+uncertainty))+.0001,
        anchor_count=len(rows),maximum_anchor_residual_ms=float(residual_ms.max()),
        note='Validity is limited to this measured clock segment; no extrapolation or filename-based alignment.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--anchors',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    with a.anchors.open(encoding='utf-8-sig',newline='') as source:rows=list(csv.DictReader(source))
    report=fit(rows,a.anchors.resolve())
    with a.output.open('x',encoding='utf-8') as target:json.dump(report,target,indent=2);target.write('\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
