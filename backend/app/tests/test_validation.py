import io
import sys
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np

# Adjust path to import app modules
repo_root = Path(__file__).resolve().parents[3]
sys.path.append(str(repo_root / "backend"))

from app.services.inference import check_image_quality, detect_vent

class TestValidationAndDetection(unittest.TestCase):
    def test_low_resolution(self):
        # 50x50 image is too small
        img = Image.new("RGB", (50, 50), color="white")
        passed, msg = check_image_quality(img)
        self.assertFalse(passed)
        self.assertIn("resolution is too low", msg)

    def test_too_dark(self):
        # average brightness < 40
        img = Image.new("RGB", (200, 200), color=(10, 10, 10))
        passed, msg = check_image_quality(img)
        self.assertFalse(passed)
        self.assertIn("too dark", msg)

    def test_too_bright(self):
        # average brightness > 240
        img = Image.new("RGB", (200, 200), color=(250, 250, 250))
        passed, msg = check_image_quality(img)
        self.assertFalse(passed)
        self.assertIn("too bright", msg)

    def test_too_blurry(self):
        # solid color image has 0 laplacian variance (blurry)
        img = Image.new("RGB", (200, 200), color=(128, 128, 128))
        passed, msg = check_image_quality(img)
        self.assertFalse(passed)
        self.assertIn("too blurry", msg)

    def test_quality_passed(self):
        # A good, sharp, balanced image
        # Create a grid pattern to ensure high Laplacian variance
        img = Image.new("RGB", (300, 300), color=(128, 128, 128))
        draw = ImageDraw.Draw(img)
        for i in range(0, 300, 20):
            draw.line([(i, 0), (i, 300)], fill=(200, 50, 50), width=3)
            draw.line([(0, i), (300, i)], fill=(50, 200, 50), width=3)
        passed, msg = check_image_quality(img)
        self.assertTrue(passed, f"Expected pass, got fail: {msg}")

    def test_detect_vent_non_vent(self):
        # A random grid pattern has high quality, but should not be detected as a vent
        img = Image.new("RGB", (300, 300), color=(128, 128, 128))
        draw = ImageDraw.Draw(img)
        for i in range(0, 300, 10):
            draw.line([(i, 0), (i, 300)], fill=(0, 0, 0), width=1)
        detected, box, cropped = detect_vent(img)
        self.assertFalse(detected)
        self.assertIsNone(box)
        self.assertIsNone(cropped)

    def test_detect_vent_actual_preset(self):
        # Load the healthy preset and verify it gets detected and cropped!
        preset_path = repo_root / "poutry_ai" / "public" / "presets" / "healthy.png"
        if not preset_path.exists():
            self.skipTest(f"Preset image not found at {preset_path}")
            
        img = Image.open(preset_path).convert("RGB")
        detected, box, cropped = detect_vent(img)
        self.assertTrue(detected, "AI detection failed to recognize a valid chicken vent image preset.")
        self.assertIsNotNone(box)
        self.assertIsNotNone(cropped)
        self.assertEqual(len(box), 4)
        
        # Verify box coordinates are percentages within 0-100
        for coord in box:
            self.assertTrue(0.0 <= coord <= 100.0)

if __name__ == "__main__":
    unittest.main()
