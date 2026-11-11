import unittest
import numpy as np

from glyphform.shapes.text_shape import (
    generate_text_mask,
    generate_text_points,
)


class TextShapeTests(unittest.TestCase):

    def test_text_mask_is_boolean(self):
        mask = generate_text_mask("ARSLAN")

        self.assertEqual(mask.dtype, bool)
        self.assertTrue(mask.any())

    def test_text_points_are_valid(self):
        points = generate_text_points("ARSLAN")

        self.assertIsInstance(points, np.ndarray)
        self.assertEqual(points.ndim, 2)
        self.assertEqual(points.shape[1], 2)
        self.assertGreater(len(points), 0)


if __name__ == "__main__":
    unittest.main()