"""Offline synthetic fixtures, explicitly not sensor/training evidence."""
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from pair_receipts import pair

NAMES=['SpineBase','SpineMid','Neck','Head','ShoulderLeft','ElbowLeft','WristLeft','HandLeft',
       'ShoulderRight','ElbowRight','WristRight','HandRight','HipLeft','KneeLeft','AnkleLeft','FootLeft',
       'HipRight','KneeRight','AnkleRight','FootRight','SpineShoulder','HandTipLeft','ThumbLeft','HandTipRight','ThumbRight']


def save(path,value):path.write_text(json.dumps(value)+'\n')


def fixture(root):
    (root/'kinect').mkdir();(root/'csi').mkdir()
    save(root/'kinect/metadata.json',dict(position_units='metres',joint_names=NAMES,host_qpc_frequency_hz=10000000,simulation=True))
    windows=[9999999,10010000,11000000,10300000,11990000]
    save(root/'csi/metadata.json',dict(windows=len(windows),qpc_frequency_hz=10000000,simulation=True))
    np.zeros((len(windows),180,60),dtype='<f4').tofile(root/'csi/tokens.f32')
    frames=[]
    for i,t in enumerate([10000000,11000000,12000000]):
        joints=[dict(name=name,x=float(i+1),y=2.,z=3.,finite=True,tracking_state='Tracked') for name in NAMES]
        if i==2:joints[NAMES.index('HandLeft')]['tracking_state']='Inferred'
        body=dict(tracking_id='actual-fixture-id',joints=joints)
        frames.append(dict(frame=i+1,host_acquire_begin_qpc=t-10,host_acquire_end_qpc=t+10,sensor_relative_ticks_100ns=t-200000,body_count=int(i!=1),bodies=[] if i==1 else [body]))
    (root/'kinect/bodies.jsonl').write_text(''.join(json.dumps(f)+'\n' for f in frames))
    (root/'csi/windows.jsonl').write_text(''.join(json.dumps(dict(record=i,frame=str(i),source_ns=str(1000000000+i*66000000),host_window_end_receipt_qpc=t,valid=True,model_prediction=[9999]*75))+'\n' for i,t in enumerate(windows)))


class ReceiptPairs(unittest.TestCase):
    def test_actual_joint_selection_and_inferred_state_are_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);fixture(root);out=root/'pairs'
            report=pair(root,out,synthetic_fixture=True)
            self.assertEqual(report['paired_windows'],2)
            np.testing.assert_array_equal(np.load(out/'csi-record-indices.npy'),[1,4])
            np.testing.assert_array_equal(np.load(out/'poses-camera-m.npy')[:,0,0],[1,3])
            np.testing.assert_array_equal(np.load(out/'reference-quality-candidate.npy'),[True,False])
            self.assertEqual(np.load(out/'tracking-states.npy')[1,NAMES.index('HandLeft')],1)
            self.assertEqual(report['rejected'],{'outside_camera_acquisition_range':1,'not_one_observed_person':1,'receipt_difference_exceeds_tolerance':1})

    def test_small_receipt_difference_does_not_certify_physical_alignment(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);fixture(root);report=pair(root,root/'pairs',synthetic_fixture=True)
            self.assertLess(report['observed_absolute_receipt_delta_ms_p50_p95_max'][-1],2)
            self.assertIsNone(report['physical_time_error_bound_ms'])
            self.assertFalse(report['RF_exposure_alignment_verified'])
            self.assertFalse(report['trainable'])
            self.assertTrue(report['synthetic_fixture'])

    def test_synthetic_data_cannot_implicitly_be_promoted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);fixture(root)
            with self.assertRaisesRegex(ValueError,'Synthetic'):pair(root,root/'pairs')

    def test_clock_domain_frequency_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);fixture(root)
            save(root/'csi/metadata.json',dict(windows=5,qpc_frequency_hz=1000000,simulation=True))
            with self.assertRaisesRegex(ValueError,'frequency'):pair(root,root/'pairs',synthetic_fixture=True)


if __name__=='__main__':unittest.main()
