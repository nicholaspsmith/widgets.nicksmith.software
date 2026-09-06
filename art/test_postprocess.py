"""Run: python3 -m unittest art/test_postprocess.py -v"""
import io
import sys
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
from gen_icons import postprocess  # noqa: E402


def synthetic_mascot() -> bytes:
    """A 400x400 white canvas with an off-center red circle and a black outline."""
    im = Image.new("RGB", (400, 400), (255, 255, 255))
    d = ImageDraw.Draw(im)
    d.ellipse((60, 90, 260, 290), fill=(220, 40, 40), outline=(0, 0, 0), width=6)
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


class PostprocessTest(unittest.TestCase):
    def test_output_is_square_rgba_at_requested_size(self):
        out = postprocess(synthetic_mascot(), size=256)
        self.assertEqual(out.mode, "RGBA")
        self.assertEqual(out.size, (256, 256))

    def test_background_is_transparent_and_subject_is_opaque(self):
        out = postprocess(synthetic_mascot(), size=256)
        for corner in [(0, 0), (255, 0), (0, 255), (255, 255)]:
            self.assertEqual(out.getpixel(corner)[3], 0, f"corner {corner} should be transparent")
        self.assertEqual(out.getpixel((128, 128))[3], 255, "subject centre should be opaque")

    def test_subject_is_centered_after_trim(self):
        out = postprocess(synthetic_mascot(), size=256)
        left, top, right, bottom = out.getchannel("A").getbbox()
        self.assertAlmostEqual(left, 256 - right, delta=3)
        self.assertAlmostEqual(top, 256 - bottom, delta=3)


if __name__ == "__main__":
    unittest.main()
