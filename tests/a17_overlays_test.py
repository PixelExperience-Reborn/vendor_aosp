#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Runtime resource overlays of the PE product on Android 17 (overlay/a17).

They replace the legacy static overlay/common, which stays opt-in behind
PE_A17_PORT_LEGACY_OVERLAYS. Every resource they set must exist in its target
on Android 17 (checked against android-17.0.0_r1): a name the target no
longer defines is ignored at runtime and the value lost. Add a name to
VERIFIED_A17 only after checking it there.
"""
from pathlib import Path
import importlib.util
import re
import struct
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OVERLAYS = ROOT / "overlay/a17"
ANDROID_NS = "{http://schemas.android.com/apk/res/android}"

VERIFIED_A17 = {
    "android": {"config_enableMultiUserUI", "config_multiuserMaximumUsers",
                "config_supportLongPressPowerWhenNonInteractive", "config_ntpServers",
                "config_enableAutoPowerModes"},
    "com.android.providers.settings": {"def_immersive_mode_confirmations"},
}
# Legacy overlay/common names Android 17 does not define, or that belong to a
# device tree, or to MindTheGapps' own overlays (config_persistentDataPackageName).
NOT_HERE = {"global_device_configs_override", "config_globallyDisabledComponents", "config_ntpServer",
            "config_lockscreenAntiFalsingClassifierEnabled", "config_gesture_settings_enabled",
            "status_bar_height_default", "status_bar_height_portrait", "config_setColorTransformAccelerated",
            "config_persistentDataPackageName"}
EXPECTED = {"FrameworksResPixelExperience", "FrameworksResPixelExperienceGms",
            "SettingsProviderResPixelExperience"}

_spec = importlib.util.spec_from_file_location("a17_common_port_test", Path(__file__).with_name(
    "a17_common_port_test.py"))
_common = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_common)


class Aosp17OverlaysTest(unittest.TestCase):
    def test_overlays_are_valid_and_verified(self):
        found = {d.name for d in OVERLAYS.iterdir() if d.is_dir()}
        self.assertEqual(found, EXPECTED)
        packages = set()
        for name in sorted(found):
            with self.subTest(overlay=name):
                d = OVERLAYS / name
                self.assertRegex((d / "Android.bp").read_text(),
                                 rf'runtime_resource_overlay \{{\s+name: "{name}",\s+product_specific: true,\s+\}}')
                manifest = ET.parse(d / "AndroidManifest.xml").getroot()
                overlay = manifest.find("overlay")
                attrs = {k.replace(ANDROID_NS, ""): v for k, v in overlay.attrib.items()}
                self.assertEqual(attrs["isStatic"], "true")
                self.assertNotIn(manifest.get("package"), packages)
                packages.add(manifest.get("package"))
                target = attrs["targetPackage"]
                for f in sorted((d / "res").glob("values*/*.xml")):
                    for element in ET.parse(f).getroot():
                        n = element.get("name")
                        self.assertIn(n, VERIFIED_A17[target], f"{f}: {n}")
                        self.assertNotIn(n, NOT_HERE)

    def test_default_wallpaper(self):
        """The PE default wallpaper (home and lock screen: Android 17 uses
        R.drawable.default_wallpaper for both). A portrait sRGB PNG of about
        the phone aspect ratio, without metadata chunks."""
        res = OVERLAYS / "FrameworksResPixelExperience/res"
        drawables = sorted(str(f.relative_to(res)) for f in res.glob("drawable*/*"))
        self.assertEqual(drawables, ["drawable-nodpi/default_wallpaper.png"])
        data = (res / "drawable-nodpi/default_wallpaper.png").read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        chunks, i = [], 8
        while i < len(data):
            length, kind = struct.unpack(">I4s", data[i:i + 8])
            chunks.append(kind.decode())
            i += 12 + length
        self.assertEqual(set(chunks), {"IHDR", "sRGB", "IDAT", "IEND"})
        width, height = struct.unpack(">II", data[16:24])
        self.assertGreaterEqual(width, 1080)
        self.assertAlmostEqual(width / height, 9 / 20, delta=0.01)

    def test_ntp_servers_of_china_keep_a_fallback(self):
        root = ET.parse(OVERLAYS / "FrameworksResPixelExperience/res/values-mcc460/config.xml").getroot()
        servers = [i.text for i in root.find("string-array[@name='config_ntpServers']")]
        self.assertTrue(all(re.fullmatch(r"ntp://[a-z0-9.-]+", s) for s in servers), servers)
        self.assertEqual(servers[-1], "ntp://time.android.com")


class Aosp17OverlaysInProduct(unittest.TestCase):
    # The product make harness of a17_common_port_test, without its tests.
    setUp = _common.HistoricalPeCommonOnAosp17.setUp
    make = _common.HistoricalPeCommonOnAosp17.make

    def packages(self, **variables):
        p = self.make(**variables)
        self.assertEqual(p.returncode, 0, p.stderr)
        line = next(l for l in p.stdout.splitlines() if l.startswith("PACKAGES="))
        return set(line.split("=", 1)[1].split())

    def test_vanilla_edition(self):
        packages = self.packages(WITH_GMS="false")
        self.assertLessEqual({"FrameworksResPixelExperience", "SettingsProviderResPixelExperience"}, packages)
        self.assertNotIn("FrameworksResPixelExperienceGms", packages)

    def test_gapps_edition(self):
        gapps = self.root / "vendor/gapps/arm64"
        gapps.mkdir(parents=True)
        (gapps / "arm64-vendor.mk").write_text("PRODUCT_PACKAGES += Phonesky\n")
        packages = self.packages(WITH_GMS="true")
        self.assertLessEqual({"FrameworksResPixelExperience", "SettingsProviderResPixelExperience",
                              "FrameworksResPixelExperienceGms", "Phonesky"}, packages)


if __name__ == "__main__":
    unittest.main()
