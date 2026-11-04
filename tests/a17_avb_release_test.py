#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Unit tests for A17 AVB config and metadata inspection (no real signing)."""
import importlib.util
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AVB = ROOT / 'config' / 'BoardConfigAvb.mk'
PREFLIGHT = ROOT / 'tools' / 'a17_release_preflight.py'
spec = importlib.util.spec_from_file_location('a17_release_preflight', PREFLIGHT)
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


class AVBTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.key = Path(self.dir.name) / 'release.pem'
        self.key.write_text('Dummy key for Make variable unit tests, not a private key.\n')

    def run_make(self, extra=''):
        content = 'BOARD_AVB_ENABLE := true\n'
        content += 'BOARD_AVB_ALGORITHM := SHA256_RSA4096\n'
        content += f'BOARD_AVB_KEY_PATH := {self.key}\n'
        content += extra + '\n'
        content += f'include {AVB}\n'
        content += 'all:\n\t@echo VALID\n'
        return subprocess.run(['make', '-s', '-f', '-', 'all'], input=content,
                              text=True, capture_output=True, cwd=self.dir.name)

    def test_explicit_key_passes_without_mutating_values(self):
        p = self.run_make()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn('VALID', p.stdout)

    def test_missing_primary_key_fails(self):
        self.key.unlink()
        p = self.run_make()
        self.assertNotEqual(p.returncode, 0)

    def test_disabled_verification_fails(self):
        p = self.run_make('BOARD_AVB_MAKE_VBMETA_IMAGE_ARGS := --flags 3')
        self.assertNotEqual(p.returncode, 0)

    def test_public_test_key_fails(self):
        p = self.run_make('BOARD_AVB_VBMETA_SYSTEM_KEY_PATH := external/avb/test/data/testkey_rsa2048.pem')
        self.assertNotEqual(p.returncode, 0)

    def test_no_algorithm_fails(self):
        content = f'BOARD_AVB_ENABLE := true\nBOARD_AVB_KEY_PATH := {self.key}\ninclude {AVB}\nall:\n\t@echo NO\n'
        p = subprocess.run(['make', '-s', '-f', '-', 'all'], input=content,
                           text=True, capture_output=True, cwd=self.dir.name)
        self.assertNotEqual(p.returncode, 0)

    def test_missing_part_key_fails(self):
        p = self.run_make('BOARD_AVB_VBMETA_SYSTEM_KEY_PATH := /not/found/pe-a17-vbmeta.pem')
        self.assertNotEqual(p.returncode, 0)


class ArchiveTests(unittest.TestCase):
    def make_zip(self, entries):
        f = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
        self.addCleanup(lambda: Path(f.name).unlink(missing_ok=True))
        f.close()
        with zipfile.ZipFile(f.name, 'w') as z:
            for name, content in entries.items():
                z.writestr(name, content)
        return f.name

    def test_release_metadata_structure(self):
        t = self.make_zip({'META/misc_info.txt':
            'avb_enable=true\nab_update=true\navb_vbmeta_key_path=/secure/release.pem\n'
            'default_system_dev_certificate=/secure/releasekey\n',
            'META/ab_partitions.txt': 'boot\nsystem\n',
            'META/otakeys.txt': 'release.x509.pem'})
        o = self.make_zip({'payload.bin': b'not a real OTA',
                           'payload_properties.txt': 'FILE_HASH=dummy',
                           'META-INF/com/android/metadata': 'ota-type=AB'})
        report = preflight.inspect(t, o)
        self.assertFalse(report['errors'], report)

    def test_public_keys_rejected(self):
        t = self.make_zip({'META/misc_info.txt': 'avb_enable=true\nab_update=false\n'
                           'avb_vbmeta_key_path=external/avb/test/data/testkey_rsa2048.pem\n'})
        self.assertTrue(preflight.inspect(t)['errors'])

    def test_verification_disabled_rejected(self):
        t = self.make_zip({'META/misc_info.txt': 'avb_enable=true\n'
                           'avb_vbmeta_args=--flags 3\n'})
        self.assertTrue(preflight.inspect(t)['errors'])

    def test_bad_ab_ota_rejected(self):
        t = self.make_zip({'META/misc_info.txt': 'avb_enable=true\nab_update=true\n',
                           'META/ab_partitions.txt': 'boot'})
        o = self.make_zip({'META-INF/com/android/metadata': 'ota-type=AB'})
        self.assertTrue(preflight.inspect(t, o)['errors'])

    def test_no_misc_info_rejected(self):
        t = self.make_zip({'META/whatever': 'data'})
        self.assertTrue(preflight.inspect(t)['errors'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
