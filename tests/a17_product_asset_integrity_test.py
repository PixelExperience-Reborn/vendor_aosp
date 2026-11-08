#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Source integrity checks for retained PixelExperience product assets.

This intentionally checks actual checked-in PE resources used by the original
product; it is not a substitute for Android17 Soong, product image or license
verification. A later full build must check external AOSP font module exports.
"""
from collections import Counter
from pathlib import Path
import re
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
AUDIO_MK = ROOT / "config/audio.mk"
BOOT_MK = ROOT / "config/bootanimation.mk"
FONTS_MK = ROOT / "config/fonts.mk"
COMMON_MK = ROOT / "config/common.mk"


def vendor_sources(file: Path):
    return re.findall(r"vendor/aosp/([A-Za-z0-9_./-]+)", file.read_text(encoding="utf-8"))


class PeProductAssetIntegrity(unittest.TestCase):
    def test_pe_sound_sources_exist_and_destinations_are_unique(self):
        src = AUDIO_MK.read_text(encoding="utf-8")
        records = []
        for line in src.splitlines():
            item = line.strip().rstrip("\\").strip()
            if not item.startswith("vendor/aosp/audio/"):
                continue
            left, sep, right = item.partition(":")
            self.assertEqual(sep, ":", item)
            self.assertTrue((ROOT / left.removeprefix("vendor/aosp/")).is_file(), left)
            self.assertIn("$(TARGET_COPY_OUT_PRODUCT)/media/audio/", right)
            records.append((left, right))
        self.assertGreater(len(records), 55, "historical PE sound inventory lost")
        dest = [right for _, right in records]
        self.assertEqual(len(dest), len(set(dest)), "duplicate audio destinations")

    def test_bootanimation_references_are_valid_archives(self):
        text = BOOT_MK.read_text(encoding="utf-8")
        expected = ("bootanimation_1080.zip", "bootanimation_1440.zip")
        for filename in expected:
            self.assertIn("vendor/aosp/bootanimation/" + filename, text)
            location = ROOT / "bootanimation" / filename
            self.assertTrue(location.is_file(), filename)
            self.assertTrue(zipfile.is_zipfile(location), filename)
            with zipfile.ZipFile(location) as zf:
                self.assertIn("desc.txt", zf.namelist(), filename)
                self.assertTrue(zf.testzip() is None, filename)

    def test_inherited_pe_resources_and_filenames(self):
        common = COMMON_MK.read_text(encoding="utf-8")
        for filename in ("audio.mk", "bootanimation.mk", "fonts.mk"):
            self.assertIn("vendor/aosp/config/" + filename, common)
        for config in (AUDIO_MK, BOOT_MK, FONTS_MK, COMMON_MK):
            for path in vendor_sources(config):
                full = ROOT / path
                self.assertTrue(full.exists(), f"{config.name}: missing {path}")
        # The original PE-specific fonts are local modules. All other fonts
        # come from pinned AOSP external/google-fonts sources, not this repo.
        android_mk = (ROOT / "fonts/Android.mk").read_text(encoding="utf-8")
        fonts = FONTS_MK.read_text(encoding="utf-8")
        for name in ("GoogleSans-Regular.ttf", "GoogleSans-Italic.ttf",
                     "GoogleSansClock-Regular.ttf", "GoogleSansFlex-Regular.ttf"):
            self.assertIn(name, fonts)
            self.assertIn(name, android_mk)
            self.assertTrue((ROOT / "fonts" / name).is_file())

    def test_copy_file_destinations_have_no_collisions_within_audio(self):
        targets = []
        for line in AUDIO_MK.read_text(encoding="utf-8").splitlines():
            line = line.strip().rstrip("\\").strip()
            if not line.startswith("vendor/aosp/audio/"):
                continue
            targets.append(line.split(":", 1)[1])
        duplicates = [name for name, count in Counter(targets).items() if count > 1]
        self.assertFalse(duplicates, f"duplicate audio installation paths {duplicates}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
