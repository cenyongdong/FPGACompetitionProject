"""Synthetic format/geometry tests; no sensors, actual training, or GPU."""
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from build_receipt_bundle import fit_local_frame,export_record,finalize,delay_consistency,JOINTS
from prepare_finetune import dataset_status
from test_pair_receipts import NAMES


def save(path,value):path.write_text(json.dumps(value)+'\n')


def reference(root,role='train'):
    root.mkdir();(root/'kinect').mkdir()
    save(root/'kinect/metadata.json',dict(host_qpc_frequency_hz=10000000))
    save(root/'visual-protocol.jsonl',dict(type='phase',host_qpc=1000000000,data=dict(phase=0)))
    joints=[dict(name=n,x=x,y=y,z=2.,tracking_state='Tracked',finite=True) for n,x,y in [('FootLeft',-.1,-1.2),('FootRight',.1,-1.2),('AnkleLeft',-.1,-1.1),('AnkleRight',.1,-1.1)]]
    frames=[dict(frame=i,host_acquire_end_qpc=1000000000+(10+i)*10000000,body_count=1,bodies=[dict(joints=joints)],floor_clip_plane=[0,1,0,0]) for i in range(3)]
    (root/'kinect/bodies.jsonl').write_text(''.join(json.dumps(f)+'\n' for f in frames))
    save(root.parent/'candidate-index.json',dict(recordings=[dict(directory=str(root.resolve()),suggested_split=role)]))


def pairs(root,recording):
    root.mkdir();tokens=np.arange(2*180*60,dtype='<f4').reshape(2,180,60);tokens.tofile(root/'tokens.f32')
    save(root/'pairing.json',dict(synthetic_fixture=True,session=recording,joint_names=NAMES,input_features=dict(path=str(root/'tokens.f32'),shape=[2,180,60])))
    positions=np.arange(2*25*3,dtype='<f4').reshape(2,25,3)/100;np.save(root/'poses-camera-m.npy',positions)
    np.save(root/'tracking-states.npy',np.full((2,25),2,dtype=np.uint8));np.save(root/'csi-record-indices.npy',np.array([1,0]));np.save(root/'reference-quality-candidate.npy',np.array([True,False]))
    return tokens,positions


class ReceiptBundle(unittest.TestCase):
    def test_reference_frame_preserves_metres_and_has_explicit_uncertainty(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'training';reference(root);frame=fit_local_frame([root]);m=np.asarray(frame['camera_metres_to_local_metres'])
            np.testing.assert_allclose(m[:3,:3]@m[:3,:3].T,np.eye(3),atol=1e-10)
            self.assertAlmostEqual(float((m@np.array([0,-1.2,2,1]))[2]),4.2)
            self.assertAlmostEqual(np.linalg.norm(m[:3,:3]@np.array([.3,.4,0])),.5)
            self.assertFalse(frame['official_coordinate_equivalence_verified'])
            self.assertFalse(frame['physical_floor_height_calibrated'])

    def test_validation_reference_is_not_used_for_fitting(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'validation';reference(root,'val')
            with self.assertRaisesRegex(ValueError,'Validation/test'):fit_local_frame([root])

    def test_export_uses_actual_selected_input_and_named_transformed_joints(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);ref=root/'reference';reference(ref);data=root/'data';data.mkdir();frame=fit_local_frame([ref]);save(data/'local-frame.json',frame)
            source=root/'pairs';tokens,positions=pairs(source,'fixture-training')
            with self.assertRaisesRegex(ValueError,'Synthetic'):export_record(source,data,'a','train')
            result=export_record(source,data,'a','train',allow_test_fixture=True)
            np.testing.assert_array_equal(np.load(data/'train_data/tokens/a_1.npy'),tokens[1])
            m=np.asarray(frame['camera_metres_to_local_metres']);indices=[NAMES.index(n) for n in JOINTS]
            expected=positions[0,indices]@m[:3,:3].T+m[:3,3]
            np.testing.assert_allclose(np.load(data/'train_data/keypoint/a_1.npy')[0],expected,atol=2e-7)
            self.assertEqual(result['count'],1);self.assertTrue(result['synthetic_fixture'])

    def test_fixture_and_recording_split_guards_survive_finalize(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);ref=root/'reference';reference(ref);data=root/'data';data.mkdir();save(data/'local-frame.json',fit_local_frame([ref]));source=root/'pairs';pairs(source,'fixture-a')
            export_record(source,data,'a','train',allow_test_fixture=True);export_record(source,data,'b','val',allow_test_fixture=True)
            with self.assertRaisesRegex(ValueError,'more than once'):finalize(data)
            item=json.loads((data/'records/b.json').read_text());item['original_recording']='fixture-b';save(data/'records/b.json',item)
            result=finalize(data);self.assertTrue(result['synthetic_fixture']);self.assertFalse(result['experimental_trainable']);self.assertFalse(dataset_status(result,True)['ready'])

    def test_receipt_profile_is_explicit_and_never_reported_certified(self):
        manifest=dict(schema='KINECT-WIFI-RECEIPT-FT1',experimental_trainable=True,trainable=False,synthetic_fixture=False)
        self.assertFalse(dataset_status(manifest)['ready'])
        self.assertEqual(dataset_status(manifest,True),dict(ready=True,certified=False,experimental=True))
        manifest['synthetic_fixture']=True;self.assertFalse(dataset_status(manifest,True)['ready'])

    def test_strict_profile_behavior_is_unchanged(self):
        self.assertEqual(dataset_status(dict(schema='KINECT-WIFI-FT1',trainable=True)),dict(ready=True,certified=True,experimental=False))

    def test_delay_outliers_are_filtered_without_certifying_constant_delay(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);save(root/'pairing.json',dict(qpc_frequency_hz=10000000))
            rows=[]
            for i in range(5):
                source=i*1000000000;receipt=100000000+source//100+(3000000 if i==4 else 0)
                rows.append(dict(pair=i,csi_source_ns=str(source),csi_receipt_qpc=receipt,kinect_acquire_begin_qpc=100000000+i*10000000,kinect_acquire_end_qpc=100000000+i*10000000,kinect_sensor_ticks_100ns=99800000+i*10000000))
            (root/'pairs.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
            allowed,report=delay_consistency(root);self.assertEqual(allowed,{0,1,2,3});self.assertEqual(report['removed'],1);self.assertIsNone(report['physical_error_bound_ms'])


if __name__=='__main__':unittest.main()
