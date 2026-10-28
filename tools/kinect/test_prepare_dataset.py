"""Synthetic format/quality tests only; no camera, CSI, model, or training."""
import json
from pathlib import Path
import struct
import tempfile
import unittest
import numpy as np
from prepare_dataset import prepare, nearest, label
from calibrate_time import fit

NAMES=['Neck','Head','ShoulderLeft','ShoulderRight','ElbowLeft','HipLeft','ElbowRight','HipRight','HandLeft','KneeLeft','HandRight','KneeRight','AnkleLeft','AnkleRight']


class PreparationTests(unittest.TestCase):
    def fixture(self,duplicate=False,unverified=False):
        parent=Path('.local/kinect-check-20261028-r1/offline-tests').resolve();parent.mkdir(exist_ok=True,parents=True)
        root=Path(tempfile.mkdtemp(prefix='pairing-fixture-',dir=parent))
        sessions=[]
        for i,split in enumerate(('train','val')):
            folder=root/split;(folder/'kinect').mkdir(parents=True);(folder/'csi').mkdir()
            domain=42 if duplicate else 42+i
            frame=dict(frame=1,sensor_relative_ticks_100ns=100000000,body_count=1,bodies=[dict(tracking_id='fixture',joints=[
                dict(name=name,index=j,x=j*.02,y=1,z=2,tracking_state='Tracked',finite=True) for j,name in enumerate(NAMES)])])
            def write(path,value):path.write_text(json.dumps(value)+'\n',encoding='utf-8')
            write(folder/'kinect/metadata.json',dict(started_utc='synthetic-'+split))
            write(folder/'kinect/result.json',dict(frames_with_bodies=1))
            write(folder/'kinect/bodies.jsonl',frame)
            write(folder/'csi/metadata.json',dict(simulation=False,synthetic_unit_fixture=True))
            write(folder/'csi/result.json',dict(records=1))
            record=bytearray(74544);struct.pack_into('<8sIIQQQQ',record,0,b'PIWFUL3\0',3,74544,domain,1,1,1000000000)
            record[384:43584]=np.full((180,60),.125,dtype='<f4').tobytes()
            # Deliberately unrelated model output: it must never become a label.
            record[44304:]=np.full((180,14,3),999,dtype='<f4').tobytes()
            (folder/'csi/actual.full').write_bytes(record)
            write(folder/'csi/arrival.jsonl',dict(valid=True,record=0,session=str(domain),frame='1',source_ns='1000000000'))
            clock=dict(verified=True,evidence='synthetic unit fixture only',input_source='live-csi',csi_session=str(domain),
                label_time_reference='window_end',reference_source_ns=1000000000,reference_kinect_ticks_100ns=100000000,
                ticks_per_source_ns=.01,max_error_ms=2,valid_source_min_ns=1000000000,valid_source_max_ns=1000000000)
            write(root/(split+'-clock.json'),clock)
            sessions.append(dict(id=split,split=split,directory=split,clock_calibration=split+'-clock.json'))
        plan=dict(synthetic_fixture=True,sessions=sessions,label_contract=dict(mapping_verified=not unverified,coordinates_verified=True,
            evidence='synthetic unit fixture only',target_joint_source_names=NAMES,camera_metres_to_model_metres=np.eye(4).tolist()))
        write(root/'plan.json',plan);return root

    def test_uses_actual_inputs_and_camera_labels_and_separates_recordings(self):
        root=self.fixture();report=prepare(root/'plan.json',root/'prepared')
        self.assertFalse(report['trainable']);self.assertTrue(report['synthetic_fixture'])
        self.assertEqual(report['counts'],{'train':1,'val':1})
        np.testing.assert_array_equal(np.load(root/'prepared/train_data/tokens/train_1.npy'),np.full((180,60),.125,dtype=np.float32))
        gt=np.load(root/'prepared/train_data/keypoint/train_1.npy');self.assertEqual(gt.shape,(1,14,3));self.assertAlmostEqual(float(gt[0,0,2]),2)

    def test_rejects_reused_csi_across_splits(self):
        root=self.fixture(duplicate=True)
        with self.assertRaisesRegex(ValueError,'reused'):prepare(root/'plan.json',root/'prepared')

    def test_rejects_unverified_joint_contract(self):
        root=self.fixture(unverified=True)
        with self.assertRaisesRegex(ValueError,'Verify'):prepare(root/'plan.json',root/'prepared')

    def test_missing_joints_are_not_filled(self):
        frame=dict(body_count=1,bodies=[dict(joints=[])])
        self.assertIsNone(label(frame,NAMES,np.eye(4)))

    def test_nearest_timestamp(self):
        self.assertEqual(nearest([100,200,300],210),1)
        self.assertIsNone(nearest([],123))

    def test_measured_clock_fit_preserves_offset_and_drift(self):
        rows=[dict(csi_session='fixture',source_ns=1000000000+i*1000000000,
            kinect_ticks_100ns=100000000+i*10000100,uncertainty_ms=1) for i in range(4)]
        clock=fit(rows,'synthetic unit fixture only')
        self.assertAlmostEqual(clock['ticks_per_source_ns'],.0100001,places=10)
        self.assertLess(clock['max_error_ms'],1.001)
        self.assertEqual(clock['valid_source_max_ns'],4000000000)


if __name__=='__main__':unittest.main()
