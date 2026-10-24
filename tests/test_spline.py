import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from tec.spline import spline

XS = [0.0, 1.0, 2.0, 3.0]
YS = [1.0, 3.0, 2.0, 5.0]
EPS = 1e-7


def derivative(f, x, side):
    return (f(x + side * EPS) - f(x)) / (side * EPS)


class SplineTest(unittest.TestCase):
    def test_passes_through_nodes(self):
        f = spline(XS, YS)
        for x, y in zip(XS, YS):
            self.assertAlmostEqual(f(x), y)

    def test_smooth_at_inner_nodes(self):
        f = spline(XS, YS)
        for x in XS[1:-1]:
            self.assertAlmostEqual(derivative(f, x, -1), derivative(f, x, 1), places=5)

    def test_start_slope_is_first_difference(self):
        f = spline(XS, YS)
        self.assertAlmostEqual(derivative(f, XS[0], 1), (YS[1] - YS[0]) / (XS[1] - XS[0]), places=5)

    def test_rejects_x_outside_nodes(self):
        f = spline(XS, YS)
        for x in (XS[0] - EPS, XS[-1] + EPS):
            with self.assertRaises(ValueError):
                f(x)


if __name__ == '__main__':
    unittest.main()
