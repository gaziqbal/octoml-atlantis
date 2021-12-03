import unittest

from atlantis.pearls import Pearl, PearlColor, PearlLayer


class TestPearls(unittest.TestCase):
    def test_pearls(self):
        p_empty = Pearl(0, [])
        self.assertTrue(p_empty.digested)
        self.assertEqual(p_empty.remaining_thickness, 0)

        p1 = Pearl(0, [PearlLayer(PearlColor.Blue, 1)])
        self.assertFalse(p1.digested)
        self.assertEqual(p1.remaining_thickness, 1)
        p1.layers[0].thickness = 0
        self.assertTrue(p1.digested)

        p2 = Pearl(0, [PearlLayer(PearlColor.Blue, 1), PearlLayer(PearlColor.Green, 2)])
        self.assertFalse(p2.digested)
        self.assertEqual(p2.remaining_thickness, 3)
        p2.layers.pop(0)
        self.assertEqual(p2.remaining_thickness, 2)
