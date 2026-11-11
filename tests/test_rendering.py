import unittest

from glyphform.rendering.screen import Screen, to256


class RenderingTests(unittest.TestCase):
    def test_rgb_to_256_colour_index_is_in_range(self):
        for rgb in ((0, 0, 0), (255, 255, 255), (255, 0, 128), (12, 80, 200)):
            with self.subTest(rgb=rgb):
                value = to256(*rgb)
                self.assertGreaterEqual(value, 16)
                self.assertLessEqual(value, 231)

    def test_poll_parses_keyboard_navigation_and_quit(self):
        screen = Screen()
        screen.read_raw = lambda: "nppq"
        event = screen.poll()
        self.assertTrue(event["quit"])
        self.assertEqual(event["step"], -1)


if __name__ == "__main__":
    unittest.main()
