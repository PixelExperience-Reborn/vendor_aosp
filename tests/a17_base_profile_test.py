#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Hermetic GNU Make checks of the standalone PE-Reborn AOSP17 product base.

Tests product inheritance only. No Android Soong bootstrap or device is built.
"""
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "config/a17_base.mk"


class Aosp17BaseProduct(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="pe-a17-base-")
        self.addCleanup(self.tmp.cleanup)
        self.cwd = Path(self.tmp.name)
        (self.cwd / "vendor").mkdir()
        (self.cwd / "vendor/aosp").symlink_to(ROOT, target_is_directory=True)

    def evaluate(self, *, with_gms=False, with_stub=False):
        if with_stub:
            p = self.cwd / "vendor/gms/products"
            p.mkdir(parents=True)
            (p / "gms.mk").write_text(
                "PRODUCT_PACKAGES += CI_DUMMY_GMS_SOURCE_MARKER\n",
                encoding="utf-8",
            )
        makefile = self.cwd / "Makefile"
        makefile.write_text(
            "define inherit-product\n"
            "$(eval include $(1))\n"
            "endef\n"
            "CUSTOM_BUILD := generic_test\n"
            "PLATFORM_VERSION := 17\n"
            "SOURCE_DATE_EPOCH := 1762108800\n"
            f"WITH_GMS := {'true' if with_gms else 'false'}\n"
            "include vendor/aosp/config/a17_base.mk\n"
            "all:\n"
            "\t@printf '%s\\n' 'BRAND=$(PRODUCT_BRAND)' "
            "'PACKAGES=$(strip $(PRODUCT_PACKAGES))' "
            "'PROPERTIES=$(strip $(PRODUCT_SYSTEM_PROPERTIES))'\n",
            encoding="utf-8",
        )
        return subprocess.run(
            ["make", "--no-print-directory", "-s", "all"],
            cwd=self.cwd, text=True, capture_output=True, timeout=20, check=False,
        )

    def test_stock_aosp17_without_gms_or_legacy_packages(self):
        p = self.evaluate()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("BRAND=PixelExperience", p.stdout)
        self.assertIn("PACKAGES=\n", p.stdout)
        self.assertIn("ro.control_privapp_permissions=enforce", p.stdout)
        self.assertIn("org.pixelexperience.version=seventeen", p.stdout)
        self.assertIn("PixelExperience_generic_test-17.0-", p.stdout)
        for forbidden in ("FaceUnlockService", "Aperture", "TouchGestures",
                          "SystemUIGoogle", "SettingsGoogle", "NexusLauncher"):
            self.assertNotIn(forbidden, p.stdout)

    def test_missing_licensed_gms_fails_fast(self):
        p = self.evaluate(with_gms=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("WITH_GMS=true requires a licensed", p.stderr)

    def test_gms_is_explicit_opt_in_and_separately_sourced(self):
        p = self.evaluate(with_gms=True, with_stub=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("CI_DUMMY_GMS_SOURCE_MARKER", p.stdout)

    def test_base_has_no_legacy_package_or_boardconfig_imports(self):
        text = BASE.read_text(encoding="utf-8")
        active = "\n".join(line.split("#", 1)[0] for line in text.splitlines())
        self.assertNotRegex(active, r"(?m)^\s*PRODUCT_PACKAGES\s*[:+?]?=")
        for path in ("config/common.mk", "rro_overlays.mk", "BoardConfig",
                     "vendor/pixel-framework", "vendor/lineage", "device/xiaomi/"):
            self.assertNotIn(path, active)
        self.assertNotIn("persist.sys.disable_rescue", active)
        self.assertNotRegex(active, r"BOARD_AVB_\w+\s*[:+?]?=")


if __name__ == "__main__":
    unittest.main(verbosity=2)
