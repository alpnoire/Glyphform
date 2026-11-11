import unittest

import numpy as np

from glyphform.shapes import RAMPS, SCENES, heart, rocket, shield, star, smoothstep


class ShapeTests(unittest.TestCase):
    def setUp(self):
        axis = np.linspace(-1.2, 1.2, 81)
        self.x, self.y = np.meshgrid(axis, axis)

    def test_all_builtin_shapes_return_nonempty_boolean_masks(self):
        for name, shape, _palette in SCENES:
            with self.subTest(shape=name):
                mask = shape(self.x, self.y)
                self.assertEqual(mask.shape, self.x.shape)
                self.assertEqual(mask.dtype, np.bool_)
                self.assertGreater(int(mask.sum()), 0)

    def test_shape_functions_are_available(self):
        self.assertTrue(callable(heart))
        self.assertTrue(callable(star))
        self.assertTrue(callable(shield))
        self.assertTrue(callable(rocket))

    def test_colour_ramps_have_expected_shape_and_range(self):
        self.assertEqual(len(RAMPS), len(SCENES))
        for ramp in RAMPS:
            self.assertEqual(ramp.shape, (40, 3))
            self.assertTrue(np.isfinite(ramp).all())
            self.assertGreaterEqual(float(ramp.min()), 0.0)
            self.assertLessEqual(float(ramp.max()), 255.0)

    def test_smoothstep_clamps_and_interpolates(self):
        values = smoothstep(0.0, 1.0, np.array([-1.0, 0.5, 2.0]))
        np.testing.assert_allclose(values, [0.0, 0.5, 1.0])


if __name__ == "__main__":
    unittest.main()
