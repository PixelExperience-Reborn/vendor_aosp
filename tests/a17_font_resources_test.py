#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Validate archived PE font configuration before Android17 product packaging.

These are source/format tests only. License, Soong module ownership, font
rasterization, and Android17 runtime rendering still need separate review.
"""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
XML = ROOT / "fonts/fonts_customization.xml"
MAKE = ROOT / "config/fonts.mk"


class PeFontConfig(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = ET.parse(XML)
        cls.root = cls.tree.getroot()

    def test_named_families_are_valid_and_no_stray_data(self):
        self.assertEqual(self.root.tag, "fonts-modification")
        self.assertEqual(self.root.attrib.get("version"), "1")
        families = self.root.findall("family")
        self.assertGreater(len(families), 5)
        names = [f.get("name") for f in families]
        self.assertEqual(len(set(names)), len(names), "duplicate named family")
        for family in families:
            self.assertFalse((family.text or "").strip(),
                             f"stray text in font family {family.get('name')}")
            self.assertGreater(len(family.findall("font")), 0)

    def test_aliases_do_not_self_reference_or_shadow_real_families(self):
        names = {f.get("name") for f in self.root.findall("family")}
        aliases = self.root.findall("alias")
        self.assertGreater(len(aliases), 2)
        seen = set()
        for alias in aliases:
            name, target = alias.get("name"), alias.get("to")
            self.assertNotEqual(name, target, "redundant/cyclic self alias")
            self.assertIn(target, names, f"undefined family {target}")
            self.assertNotIn(name, names, f"alias shadows family {name}")
            self.assertNotIn(name, seen, f"duplicate alias {name}")
            seen.add(name)

    def test_every_installed_font_reference_is_in_pe_font_package_list(self):
        source = MAKE.read_text(encoding="utf-8")
        packages = set(re.findall(r"[A-Za-z0-9_-]+\.ttf", source))
        xml_fonts = set()
        for font in self.root.iter("font"):
            path = (font.text or "").strip()
            self.assertRegex(path, r"^[A-Za-z0-9_-]+\.ttf$")
            xml_fonts.add(path)
        self.assertTrue(xml_fonts.issubset(packages),
                        f"unpackaged referenced fonts: {sorted(xml_fonts-packages)}")

    def test_pe_google_font_modules_remain_in_archive(self):
        bp = (ROOT / "fonts/Android.mk").read_text(encoding="utf-8")
        for font in ("GoogleSans-Regular.ttf", "GoogleSans-Italic.ttf",
                     "GoogleSansClock-Regular.ttf", "GoogleSansFlex-Regular.ttf"):
            self.assertIn(font, bp)
            self.assertTrue((ROOT / "fonts" / font).is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)
