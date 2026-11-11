import unittest

import numpy as np

from glyphform.engine import World


class WorldTests(unittest.TestCase):
    def setUp(self):
        self.world = World(80, 24, np.random.default_rng(7))

    def test_world_builds_a_mask_for_each_scene(self):
        self.assertEqual(len(self.world.masks), 4)
        self.assertEqual(len(self.world.edges), 4)
        for mask in self.world.masks:
            self.assertEqual(mask.shape, (24, 80))
            self.assertTrue(mask.any())

    def test_simulation_and_frame_have_expected_dimensions(self):
        glyphs, colours, ramp, force = self.world.frame(0.0, 1.0 / 30.0)
        self.assertEqual(glyphs.shape, (24, 80))
        self.assertEqual(colours.shape, (24, 80))
        self.assertEqual(ramp.shape, (40, 3))
        self.assertEqual(glyphs.dtype, np.uint8)
        self.assertEqual(colours.dtype, np.uint8)
        self.assertTrue(np.isfinite(self.world.pos).all())
        self.assertTrue(np.isfinite(self.world.vel).all())

    def test_scene_can_be_advanced_explicitly(self):
        self.world.step(0.0, 1.0 / 30.0)  # Initialize the first scene.
        self.world.handle({"quit": False, "step": 1, "pos": None, "left": None}, 0.1)
        self.world.step(0.1, 1.0 / 30.0)
        self.assertEqual(self.world.scene, 1)


if __name__ == "__main__":
    unittest.main()
