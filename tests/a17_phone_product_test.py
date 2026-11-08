#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""PE phone product Make policy gates; host-only Android17 integration smoke."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PePhoneProduct(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory(prefix="pe-a17-phone-")
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        (self.root / "vendor").mkdir()
        (self.root / "vendor/aosp").symlink_to(ROOT, target_is_directory=True)

    def build(self, bypass=False):
        src = (
            "define inherit-product\n"
            "$(eval include $(1))\n"
            "endef\n"
            "CUSTOM_BUILD := a17phone\n"
            "SOURCE_DATE_EPOCH := 1762108800\n"
            "TARGET_COPY_OUT_SYSTEM_EXT := system_ext\n"
            "TARGET_COPY_OUT_PRODUCT := product\n"
            "TARGET_COPY_OUT_SYSTEM := system\n"
            f"PE_A17_PORT_LEGACY_TETHERING_BYPASS := {'true' if bypass else 'false'}\n"
            "include vendor/aosp/config/common_full_phone.mk\n"
            "all:\n"
            "\t@printf '%s\\n' 'PHONE=$(IS_PHONE)' "
            "'PACKAGES=$(strip $(PRODUCT_PACKAGES))' "
            "'SYSTEM=$(strip $(PRODUCT_SYSTEM_PROPERTIES))' "
            "'DEFAULT=$(strip $(PRODUCT_SYSTEM_DEFAULT_PROPERTIES))'\n"
        )
        (self.root / "Makefile").write_text(src, encoding="utf-8")
        return subprocess.run(
            ["make", "--no-print-directory", "-s", "all"],
            cwd=self.root, capture_output=True, text=True, timeout=20,
            check=False,
        )

    def test_phone_inherits_full_pe_product_without_default_carrier_bypass(self):
        p = self.build()
        self.assertEqual(p.returncode, 0, p.stderr)
        for item in ("PHONE=true", "Stk", "apns-conf.xml",
                     "org.pixelexperience.version=seventeen",
                     "ro.control_privapp_permissions=enforce"):
            self.assertIn(item, p.stdout)
        self.assertNotIn("net.tethering.noprovisioning", p.stdout)

    def test_legacy_tethering_exception_must_be_explicit(self):
        p = self.build(bypass=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("net.tethering.noprovisioning=true", p.stdout)
        self.assertEqual(p.stdout.count("net.tethering.noprovisioning=true"), 1)

    def test_no_unreviewed_default_legacy_modules_in_phone_profile(self):
        p = self.build()
        self.assertEqual(p.returncode, 0, p.stderr)
        for name in ("TouchGestures", "FaceUnlockService", "Aperture",
                     "SettingsGoogle", "SystemUIGoogle"):
            self.assertNotIn(name, p.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
