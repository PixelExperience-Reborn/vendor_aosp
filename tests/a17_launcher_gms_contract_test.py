#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""PE-Reborn AOSP17 launcher/GMS product boundary — GNU Make fixture only.

Checks actual PRODUCT_PACKAGES and dexpreopt expansion from the staged
common.mk, without importing proprietary Google source or any device tree.
This does NOT compile Launcher3, validate Quickstep runtime or ship an APK.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
COMMON = ROOT / "config/common.mk"


class Aosp17LauncherGmsContract(unittest.TestCase):
    def setUp(self):
        context = tempfile.TemporaryDirectory(prefix="pe-a17-home-gms-")
        self.addCleanup(context.cleanup)
        self.work = Path(context.name)
        (self.work / "vendor").mkdir()
        (self.work / "vendor/aosp").symlink_to(ROOT, target_is_directory=True)

    def product(self, variables=None, gms_fixture=None, product="common"):
        if gms_fixture is not None:
            p = self.work / "vendor/gms/products"
            p.mkdir(parents=True, exist_ok=True)
            (p / "gms.mk").write_text(gms_fixture, encoding="utf-8")
        var = variables or {}
        source = {
            "common": "vendor/aosp/config/common.mk",
            "phone": "vendor/aosp/config/common_full_phone.mk",
            "full": "vendor/aosp/config/common_full.mk",
        }[product]
        lines = [
            "define inherit-product",
            "$(eval include $(1))",
            "endef",
            "CUSTOM_BUILD := test_home",
            "SOURCE_DATE_EPOCH := 1762108800",
            "TARGET_COPY_OUT_SYSTEM_EXT := system_ext",
            "TARGET_COPY_OUT_PRODUCT := product",
            "TARGET_COPY_OUT_SYSTEM := system",
        ]
        lines += [f"{k} := {v}" for k, v in var.items()]
        lines += [
            f"include {source}",
            "all:",
            "\t@printf '%s\\n' 'PACKAGES=$(strip $(PRODUCT_PACKAGES))' "
            "'DEXPREOPT=$(strip $(PRODUCT_DEXPREOPT_SPEED_APPS))' "
            "'OVERLAYS=$(strip $(PRODUCT_PACKAGE_OVERLAYS))' "
            "'PROPERTIES=$(strip $(PRODUCT_PRODUCT_PROPERTIES) "
            "$(PRODUCT_SYSTEM_PROPERTIES))'",
        ]
        (self.work / "Makefile").write_text("\n".join(lines) + "\n",
                                            encoding="utf-8")
        return subprocess.run(
            ["make", "--no-print-directory", "-s", "all"],
            cwd=self.work, capture_output=True, text=True, timeout=25,
            check=False,
        )

    def line_tokens(self, out, key):
        line = next((s for s in out.splitlines() if s.startswith(key + "=")),
                    None)
        self.assertIsNotNone(line, out)
        return line.partition("=")[2].split()

    def test_gms_free_product_has_one_aosp17_launcher_quickstep(self):
        for args in ({}, {"WITH_GMS": "false"}):
            with self.subTest(args=args):
                process = self.product(args)
                self.assertEqual(process.returncode, 0, process.stderr)
                packages = self.line_tokens(process.stdout, "PACKAGES")
                self.assertEqual(packages.count("Launcher3QuickStep"), 1)
                for denied in ("Launcher3", "Launcher3Go", "Launcher3QuickStepGo",
                               "NexusLauncherRelease", "SystemUIGoogle",
                               "PixelLauncherCustomOverlay", "NexusLauncherResOverlay"):
                    self.assertNotIn(denied, packages)
                self.assertNotIn("vendor/gms", process.stdout)
                self.assertNotIn("ro.com.google.clientidbase=", process.stdout)
                self.assertNotIn("NexusLauncherRelease",
                                 self.line_tokens(process.stdout, "DEXPREOPT"))

    def test_full_and_phone_product_inherit_native_aosp_launcher_once(self):
        for kind in ("full", "phone"):
            with self.subTest(product=kind):
                p = self.product(product=kind)
                self.assertEqual(p.returncode, 0, p.stderr)
                self.assertEqual(
                    self.line_tokens(p.stdout, "PACKAGES").count("Launcher3QuickStep"),
                    1,
                )

    def test_gms_flag_with_missing_license_source_fails_fast(self):
        p = self.product({"WITH_GMS": "true"})
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("requires a licensed vendor/gms/products/gms.mk", p.stderr)

    def test_gms_source_is_opt_in_and_native_home_remains_available(self):
        stub = "PRODUCT_PACKAGES += CI_GMS_FIXTURE\n"
        p = self.product({"WITH_GMS": "true"}, gms_fixture=stub)
        self.assertEqual(p.returncode, 0, p.stderr)
        packages = self.line_tokens(p.stdout, "PACKAGES")
        self.assertIn("CI_GMS_FIXTURE", packages)
        self.assertEqual(packages.count("Launcher3QuickStep"), 1)
        self.assertNotIn("NexusLauncherRelease", packages)
        self.assertIn("ro.com.google.clientidbase=", p.stdout)
        self.assertNotIn("NexusLauncherRelease",
                         self.line_tokens(p.stdout, "DEXPREOPT"))

    def test_google_privapp_preopt_requires_both_explicit_gates(self):
        stub = "PRODUCT_PACKAGES += CI_GMS_FIXTURE\n"
        for flagset in (
            {"WITH_GMS": "false", "PE_A17_PORT_GOOGLE_PRIV_APPS": "true"},
            {"WITH_GMS": "true"},
        ):
            with self.subTest(flagset=flagset):
                # A dummy licensed source is used for the GMS flag, no APK.
                p = self.product(flagset, gms_fixture=stub)
                self.assertEqual(p.returncode, 0, p.stderr)
                preopt = self.line_tokens(p.stdout, "DEXPREOPT")
                self.assertNotIn("NexusLauncherRelease", preopt)
                self.assertNotIn("SystemUIGoogle", preopt)
        p = self.product({"WITH_GMS": "true",
                          "PE_A17_PORT_GOOGLE_PRIV_APPS": "true"},
                         gms_fixture=stub)
        self.assertEqual(p.returncode, 0, p.stderr)
        preopt = self.line_tokens(p.stdout, "DEXPREOPT")
        self.assertIn("NexusLauncherRelease", preopt)
        self.assertIn("SystemUIGoogle", preopt)
        # Preopt is not installation: no Pixel APK is supplied by this stub.
        self.assertNotIn("NexusLauncherRelease",
                         self.line_tokens(p.stdout, "PACKAGES"))

    def test_pixel_rro_requires_a_separate_explicit_gate(self):
        stub = "PRODUCT_PACKAGES += CI_GMS_FIXTURE\n"
        p = self.product({"WITH_GMS": "true"}, gms_fixture=stub)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("PixelLauncherCustomOverlay",
                         self.line_tokens(p.stdout, "PACKAGES"))
        enabled = self.product({"WITH_GMS": "true",
                                "PE_A17_PORT_LEGACY_OVERLAYS": "true"},
                               gms_fixture=stub)
        self.assertEqual(enabled.returncode, 0, enabled.stderr)
        self.assertIn("PixelLauncherCustomOverlay",
                      self.line_tokens(enabled.stdout, "PACKAGES"))
        # Enabling it is NOT proof that its Google target packages exist.

    def test_dont_reintroduce_old_launcher_or_proprietary_prebuilts(self):
        text = COMMON.read_text(encoding="utf-8")
        self.assertIn("Launcher3QuickStep", text)
        self.assertIn("vendor/gms/products/gms.mk", text)
        self.assertNotIn("packages_apps_Launcher3", text)
        self.assertNotIn("git clone", text)
        self.assertNotIn("curl ", text)
        self.assertNotIn("ro.adb.secure=0", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
