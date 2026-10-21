import unittest

import numpy as np

from native_carriers import select_packed
from map_node_windows import HT20_NG2


class CarrierIntegrity(unittest.TestCase):
    def test_explicit_ng2_profile(self):
        self.assertEqual(len(HT20_NG2),30)
        self.assertEqual(HT20_NG2[:3],(-28,-26,-24))
        self.assertEqual(HT20_NG2[14:17],(-1,1,3))
        self.assertEqual(HT20_NG2[-2:],(27,28))

    def test_endpoint_requires_original_and_source_is_unchanged(self):
        # This fixture is an explicit test profile, not an asserted training map.
        carriers=list(range(-28,-14))+[-1]+list(range(1,15))+[28]
        words=np.arange(3*64,dtype='u4').reshape(3,64)
        before=words.copy()
        with self.assertRaises(ValueError):
            select_packed(words,carriers)
        original=np.full((3,3),10000,dtype='u4')
        selected=select_packed(words,carriers,original)
        self.assertEqual(selected.shape,(3,30))
        np.testing.assert_array_equal(selected[:,-1],original[:,0])
        np.testing.assert_array_equal(selected[:,0],words[:,36])
        np.testing.assert_array_equal(words,before)

    def test_no_profile_guessing_or_dc_or_repeated_carrier(self):
        words=np.ones((3,64),dtype='u4')
        for carriers in ([],list(range(30)),[-1]*30):
            with self.assertRaises(ValueError):
                select_packed(words,carriers)


if __name__=='__main__':
    unittest.main()
