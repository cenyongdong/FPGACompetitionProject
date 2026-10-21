import unittest

import numpy as np

from map_node_windows import HT20_NG2
from single_node_adapter import SingleNodeAdapter
from stream_time_grid import Observation,Window


def profile():
    return dict(schema=1,method='fixed_shared_empirical_gain',gain=8.5,
        receiver_nodes=1,physical_power_calibrated=False,signed_carriers=HT20_NG2,
        transmitter_mac='50:bb:b5:db:a5:02',chanspec=0xd095)


class SingleNodeScale(unittest.TestCase):
    def test_fixed_gain_preserves_phase_ratios_and_source(self):
        rng=np.random.default_rng(21)
        x=rng.normal(size=(2,3,30,20))+1j*rng.normal(size=(2,3,30,20))
        saved=x.copy();a=SingleNodeAdapter(profile());y=a.apply(x)
        np.testing.assert_array_equal(x,saved)
        self.assertLess(float(np.max(np.abs(np.angle(y*np.conj(x))))),3e-16)
        np.testing.assert_allclose(y[:,1]/y[:,0],x[:,1]/x[:,0],atol=1e-14,rtol=1e-14)
        np.testing.assert_array_equal(y,x*8.5)

    def test_profile_and_input_rejections(self):
        for key,value in [('gain',0),('gain',float('nan')),('physical_power_calibrated',True),('signed_carriers',list(range(30)))]:
            p=profile();p[key]=value
            with self.assertRaises(ValueError):SingleNodeAdapter(p)
        a=SingleNodeAdapter(profile())
        for x in (np.zeros((3,30,20),dtype='complex128'),np.ones((3,3,30,20)),
                  np.full((3,30,20),complex(float('nan'),0))):
            with self.assertRaises(ValueError):a.apply(x)

    def test_stream_mapping_uses_each_core_original_and_rejects_missing(self):
        a=SingleNodeAdapter(profile());items=[]
        for i in range(20):
            words=np.full((3,64),1<<18,dtype='u4')
            original=np.full((3,3),2<<18,dtype='u4')
            items.append(Observation(i,i*3333,words,original))
        w=Window(0,0,tuple(items),tuple(range(20)),70000,True,'',True)
        y=a.map_window(w,profile()['transmitter_mac'],0xd095)
        self.assertEqual(y.shape,(3,30,20))
        np.testing.assert_array_equal(y[:,-1],2*y[:,-2])
        items[-1].original_words=None
        with self.assertRaises(ValueError):a.map_window(w,profile()['transmitter_mac'],0xd095)
        with self.assertRaises(ValueError):a.map_window(w,'00:11:22:33:44:55',0xd095)


if __name__=='__main__':unittest.main()
