#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""GNU Make regression tests for preserving PE legacy choices while staging AOSP17.

This checks product variable expansion and safety defaults, not Soong module
existence, APK compatibility, permissions, or an Android product build.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
COMMON = ROOT / "config/common.mk"


class HistoricalPeCommonOnAosp17(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="pe-a17-common-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "vendor").mkdir()
        (self.root / "vendor/aosp").symlink_to(ROOT, target_is_directory=True)

    def make(self, **variables):
        makefile = [
            "define inherit-product",
            "$(eval include $(1))",
            "endef",
            "CUSTOM_BUILD := test_platform",
            "SOURCE_DATE_EPOCH := 1762108800",
            "TARGET_COPY_OUT_SYSTEM_EXT := system_ext",
            "TARGET_COPY_OUT_PRODUCT := product",
            "TARGET_COPY_OUT_SYSTEM := system",
        ]
        makefile.extend(f"{key} := {value}" for key, value in variables.items())
        makefile += [
            "include vendor/aosp/config/common.mk",
            "all:",
            "\t@printf '%s\\n' 'PACKAGES=$(strip $(PRODUCT_PACKAGES))' "
            "'PROPERTIES=$(strip $(PRODUCT_SYSTEM_DEFAULT_PROPERTIES) "
            "$(PRODUCT_PRODUCT_PROPERTIES) $(PRODUCT_SYSTEM_PROPERTIES))' "
            "'COPY=$(strip $(PRODUCT_COPY_FILES))' "
            "'OVERLAYS=$(strip $(PRODUCT_PACKAGE_OVERLAYS))' "
            "'FACE=$(TARGET_FACE_UNLOCK_SUPPORTED)' "
            "'DEXPREOPT=$(strip $(PRODUCT_DEXPREOPT_SPEED_APPS))'",
        ]
        (self.root / "Makefile").write_text("\n".join(makefile) + "\n", encoding="utf-8")
        return subprocess.run(
            ["make", "--no-print-directory", "-s", "all"],
            cwd=self.root, text=True, capture_output=True, timeout=20,
            check=False,
        )

    def test_platform_default_preserves_pe_resources_without_unported_apks(self):
        p = self.make(WITH_GMS="false")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("org.pixelexperience.version=seventeen", p.stdout)
        self.assertIn("ro.control_privapp_permissions=enforce", p.stdout)
        self.assertIn("audio/alarms/A_real_hoot.ogg", p.stdout)
        self.assertIn("fonts/fonts_customization.xml", p.stdout)
        self.assertIn("FACE=false", p.stdout)
        for forbidden in (
            "TouchGestures", "FaceUnlockService", "Aperture",
            "libprotobuf-cpp-full-3.9.1-vendorcompat",
            "PixelConfigOverlayCommon", "NexusLauncherResOverlay",
            "privapp-permissions-lineagehw.xml", "SystemUIGoogle",
            "ro.adb.secure=", "persist.sys.usb.config=",
            "persist.sys.disable_rescue=true",
            "persist.sys.strictmode.disable=true",
            "ro.boot.vendor.overlay.theme=",
        ):
            self.assertNotIn(forbidden, p.stdout, forbidden)

    def test_explicit_legacy_package_candidates_are_preserved(self):
        p = self.make(WITH_GMS="false", PE_A17_PORT_TOUCH_GESTURES="true",
                      PE_A17_PORT_APERTURE="true", PE_A17_PORT_QCOM_VENDORCOMPAT="true")
        self.assertEqual(p.returncode, 0, p.stderr)
        for expected in ("TouchGestures", "Aperture", "libprotobuf-cpp-full-3.9.1-vendorcompat",
                         "libprotobuf-cpp-lite-3.9.1-vendorcompat"):
            self.assertIn(expected, p.stdout)
        self.assertNotIn("FaceUnlockService", p.stdout)

    def test_face_unlock_needs_both_port_and_hardware_selection(self):
        for extra in (
            {"PE_A17_PORT_FACE_UNLOCK": "true"},
            {"TARGET_FACE_UNLOCK_SUPPORTED": "true"},
        ):
            p = self.make(**extra)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertNotIn("FaceUnlockService", p.stdout)
        p = self.make(PE_A17_PORT_FACE_UNLOCK="true", TARGET_FACE_UNLOCK_SUPPORTED="true")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("FaceUnlockService", p.stdout)
        self.assertIn("ro.face_unlock_service.enabled=true", p.stdout)
        self.assertIn("android.hardware.biometrics.face.xml", p.stdout)

    def test_legacy_visual_overlays_are_explicit(self):
        p = self.make(PE_A17_PORT_LEGACY_OVERLAYS="true")
        self.assertEqual(p.returncode, 0, p.stderr)
        for expected in ("NexusLauncherResOverlay", "PixelConfigOverlayCommon",
                         "vendor/aosp/overlay/common"):
            self.assertIn(expected, p.stdout)

    def test_gms_without_license_fails_and_does_not_enable_privapps_by_default(self):
        p = self.make(WITH_GMS="true")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("WITH_GMS=true requires a licensed", p.stderr)

    def test_new_default_excludes_obsolete_legacy_system_modules(self):
        p = self.make()
        self.assertEqual(p.returncode, 0, p.stderr)
        for legacy in ("charger_res_images", "product_charger_res_images",
                       "fsck.ntfs", "mkfs.ntfs", "mount.ntfs",
                       "libtextclassifier_annotator_en_model",
                       "libtextclassifier_actions_suggestions_universal_model",
                       "Updates", "init.pixelexperience-updater.rc"):
            self.assertNotIn(legacy, p.stdout, legacy)
        self.assertIn("mke2fs", p.stdout)
        self.assertIn("QuickAccessWallet", p.stdout)

    def test_legacy_options_remain_available_for_reviewed_ports(self):
        p = self.make(PE_A17_PORT_LEGACY_CHARGER="true",
                      PE_A17_PORT_NTFS="true",
                      PE_A17_PORT_LEGACY_TEXTCLASSIFIER="true")
        self.assertEqual(p.returncode, 0, p.stderr)
        for expected in ("charger_res_images", "product_charger_res_images",
                         "fsck.ntfs", "mkfs.ntfs", "mount.ntfs",
                         "libtextclassifier_annotator_en_model"):
            self.assertIn(expected, p.stdout, expected)

    def test_updater_follows_release_build_and_explicit_port(self):
        p = self.make(PE_A17_PORT_UPDATER="true", CUSTOM_BUILD_TYPE="BETA")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertNotIn("init.pixelexperience-updater.rc", p.stdout)
        self.assertNotIn("Updates", p.stdout)
        p = self.make(PE_A17_PORT_UPDATER="true", CUSTOM_BUILD_TYPE="OFFICIAL")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("init.pixelexperience-updater.rc", p.stdout)
        self.assertIn("Updates", p.stdout)

    def test_android17_product_properties_do_not_duplicate_old_gms_props(self):
        p = self.make(WITH_GMS="false")
        self.assertEqual(p.returncode, 0, p.stderr)
        src = COMMON.read_text(encoding="utf-8")
        self.assertNotIn("PRODUCT_SYSTEM_DEFAULT_PROPERTIES", src)
        for legacy in ("dalvik.vm.debug.alloc=0",
                       "dalvik.vm.systemuicompilerfilter=speed",
                       "ro.com.android.dateformat=MM-dd-yyyy"):
            self.assertNotIn(legacy, src)
        self.assertEqual(p.stdout.count("ro.control_privapp_permissions=enforce"), 1)
        self.assertNotIn("ro.com.google.clientidbase=", p.stdout)

    def test_gms_product_properties_have_single_owner(self):
        stub = self.root / "vendor/gms/products"
        stub.mkdir(parents=True)
        (stub / "gms.mk").write_text(
            "PRODUCT_PACKAGES += CI_LICENSED_GMS_FIXTURE\n",
            encoding="utf-8",
        )
        p = self.make(WITH_GMS="true")
        self.assertEqual(p.returncode, 0, p.stderr)
        for key in ("ro.com.google.clientidbase=",
                    "ro.url.legal=",
                    "ro.error.receiver.system.apps=",
                    "ro.atrace.core.services="):
            self.assertEqual(p.stdout.count(key), 1, (key, p.stdout))
        self.assertIn("CI_LICENSED_GMS_FIXTURE", p.stdout)

    def test_legacy_sources_retained_for_feature_by_feature_port(self):
        source = COMMON.read_text(encoding="utf-8")
        for marker in ("TouchGestures", "Aperture", "FaceUnlockService",
                       "vendor/aosp/config/rro_overlays.mk",
                       "vendor/aosp/config/audio.mk",
                       "vendor/aosp/config/bootanimation.mk",
                       "vendor/aosp/config/fonts.mk"):
            self.assertIn(marker, source)
        self.assertNotIn("persist.sys.disable_rescue=true", source)
        self.assertNotIn("ro.adb.secure=0", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
