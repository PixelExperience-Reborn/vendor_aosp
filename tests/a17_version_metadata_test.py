#!/usr/bin/env python3
"""Stage 9 make integration tests for PE release metadata; no Android build."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BRANDING = ROOT / "config/branding.mk"
MAIN = ROOT / "build/core/main_version.mk"
COMMON = ROOT / "config/common.mk"


class VersioningTests(unittest.TestCase):
    def evaluate(self, *, patch="2026-06-05", epoch="1762108800"):
        with tempfile.TemporaryDirectory() as td:
            mk = Path(td) / "Makefile"
            mk.write_text(
                "CUSTOM_BUILD := mondrian\n"
                "PLATFORM_VERSION := 17\n"
                f"PLATFORM_SECURITY_PATCH := {patch}\n"
                f"SOURCE_DATE_EPOCH := {epoch}\n"
                f"include {BRANDING}\n"
                f"include {MAIN}\n"
                "all:\n"
                "\t@printf '%s\\n' '$(CUSTOM_VERSION)' '$(PRODUCT_SYSTEM_PROPERTIES)'\n",
                encoding="utf-8",
            )
            p = subprocess.run(["make", "--no-print-directory", "-s", "-f", str(mk)],
                               text=True, capture_output=True, timeout=15)
            self.assertEqual(p.returncode, 0, p.stderr)
            return p.stdout

    def test_version_name_and_release_label(self):
        out = self.evaluate()
        self.assertIn("PixelExperience_mondrian-17.0-", out)
        self.assertIn("org.pixelexperience.version=seventeen", out)
        self.assertIn("org.pixelexperience.build_type=BETA", out)

    def test_single_epoch_used(self):
        out = self.evaluate(epoch="0")
        self.assertIn("19700101-0000", out)
        self.assertIn("org.pixelexperience.build_date_utc=0", out)

    def test_platform_patch_only_when_present(self):
        self.assertIn("org.pixelexperience.build_security_patch=2026-06-05", self.evaluate())
        self.assertNotIn("org.pixelexperience.build_security_patch=", self.evaluate(patch=""))

    def test_no_security_or_signing_overrides(self):
        source = BRANDING.read_text() + MAIN.read_text()
        for bad in ("ro.build.fingerprint=", "BUILD_FINGERPRINT :=", "BUILD_VERSION_TAGS +=",
                    "BUILD_KEYS :=", "CUSTOM_SECURITY_PATCH := 2022-08-05",
                    "ro.build.version.security_patch="):
            self.assertNotIn(bad, source)

    def test_legacy_date_override_removed(self):
        self.assertNotIn("BUILD_UTC_DATE=0", COMMON.read_text())


if __name__ == "__main__":
    unittest.main(verbosity=2)
