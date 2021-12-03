import unittest

from atlantis.pearls import Pearl, PearlColor, PearlLayer
from atlantis.workers import GeneralWorker, VectorWorker, MatrixWorker


class TestWorkers(unittest.TestCase):
    def test_worker_costs(self):
        g = GeneralWorker(0)
        v = VectorWorker(1)
        m = MatrixWorker(2)

        # test costing
        p = Pearl(0, [PearlLayer(PearlColor.Green, 10)])
        self.assertEqual(g.cost_pearl(p), 10)
        self.assertEqual(v.cost_pearl(p), 2)
        self.assertEqual(m.cost_pearl(p), 5)

        # test ceiling
        p = Pearl(0, [PearlLayer(PearlColor.Green, 11)])
        self.assertEqual(g.cost_pearl(p), 11)
        self.assertEqual(v.cost_pearl(p), 3)
        self.assertEqual(m.cost_pearl(p), 6)

        # test two layers
        p = Pearl(
            0, [PearlLayer(PearlColor.Green, 11), PearlLayer(PearlColor.Blue, 10)]
        )
        self.assertEqual(g.cost_pearl(p), 11 + 10)
        self.assertEqual(v.cost_pearl(p), 3 + 5)
        self.assertEqual(m.cost_pearl(p), 6 + 1)

        # test two similar layers
        p = Pearl(
            0, [PearlLayer(PearlColor.Green, 11), PearlLayer(PearlColor.Green, 10)]
        )
        self.assertEqual(g.cost_pearl(p), 11 + 10)
        self.assertEqual(v.cost_pearl(p), 3 + 2)
        self.assertEqual(m.cost_pearl(p), 6 + 5)
