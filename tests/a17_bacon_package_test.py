#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Hermetic offline tests of PE's Android 17 bacon packaging adapter."""
import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pe_bacon', ROOT / 'tools/a17_bacon_package.py')
bacon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bacon)


def fake_ota(path, ab=True):
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_STORED) as z:
        if ab:
            z.writestr('payload.bin', b'CrAU\x00\x00\x00\x00')
            z.writestr('payload_properties.txt', 'FILE_HASH=TEST')
        else:
            z.writestr('META-INF/com/google/android/update-binary', b'NOT-A-REAL-UPDATER')
        z.writestr('META-INF/com/android/metadata', 'ota-type=AB\npost-build=example\n')


class Packaging(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pe-bacon-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ota = self.root / 'upstream-ota.zip'
        self.out = self.root / 'PixelExperience_mondrian-17.0-TEST-BETA.zip'
        fake_ota(self.ota)

    def test_copy_matches_original(self):
        dig = bacon.create(self.ota, self.out)
        self.assertEqual(self.out.read_bytes(), self.ota.read_bytes())
        self.assertEqual(dig, hashlib.sha256(self.ota.read_bytes()).hexdigest())
        self.assertEqual(self.out.with_name(self.out.name+'.sha256sum').read_text(), f'{dig}  {self.out.name}\n')

    def test_works_without_os_link(self):
        # Android Termux builds can have no os.link attribute at all.
        from unittest import mock
        with mock.patch.object(bacon.os, 'link', side_effect=AssertionError('os.link must not be called'), create=True):
            bacon.create(self.ota, self.out)
        self.assertEqual(self.out.read_bytes(), self.ota.read_bytes())

    def test_output_race_does_not_overwrite(self):
        # Create a competing target right before the exclusive open.
        from unittest import mock
        original_open = bacon.os.open
        def raced_open(path, flags, mode=0o777, *, dir_fd=None):
            if str(path) == str(self.out) and (flags & os.O_EXCL):
                self.out.write_bytes(b'other writer')
            if dir_fd is None:
                return original_open(path, flags, mode)
            return original_open(path, flags, mode, dir_fd=dir_fd)
        with mock.patch.object(bacon.os, 'open', side_effect=raced_open):
            with self.assertRaises(FileExistsError):
                bacon.create(self.ota, self.out)
        self.assertEqual(self.out.read_bytes(), b'other writer')

    def test_publish_copy_failure_cleans_partial(self):
        from unittest import mock
        copy_original = bacon.shutil.copyfileobj
        calls = 0
        def fail_second_copy(src, dst, length=0):
            nonlocal calls
            calls += 1
            if calls == 2:
                dst.write(b'partial')
                raise OSError('simulated output write failure')
            return copy_original(src, dst, length)
        with mock.patch.object(bacon.shutil, 'copyfileobj', side_effect=fail_second_copy):
            with self.assertRaisesRegex(OSError, 'simulated'):
                bacon.create(self.ota, self.out)
        self.assertFalse(self.out.exists())
        self.assertFalse(self.out.with_name(self.out.name + '.sha256sum').exists())

    def test_idempotent(self):
        bacon.create(self.ota, self.out)
        bacon.create(self.ota, self.out)
        self.assertEqual(self.out.read_bytes(), self.ota.read_bytes())

    def test_collision_refuses_changed_output(self):
        self.out.write_bytes(b'wrong')
        with self.assertRaisesRegex(ValueError, 'Different output'):
            bacon.create(self.ota, self.out)
        self.assertEqual(self.out.read_bytes(), b'wrong')

    def test_invalid_non_ota_zip(self):
        with zipfile.ZipFile(self.ota, 'w') as z:
            z.writestr('random.txt', 'not an OTA')
        with self.assertRaisesRegex(ValueError, 'not a valid'):
            bacon.create(self.ota, self.out)

    def test_missing_input(self):
        self.ota.unlink()
        with self.assertRaisesRegex(ValueError, 'Missing'):
            bacon.create(self.ota, self.out)

    def test_recovery_zip(self):
        fake_ota(self.ota, ab=False)
        bacon.create(self.ota, self.out)
        self.assertEqual(self.out.read_bytes(), self.ota.read_bytes())

    def test_symlink_ota_rejected(self):
        link = self.root / 'link.zip'
        link.symlink_to(self.ota)
        with self.assertRaisesRegex(ValueError, 'symlinked'):
            bacon.create(link, self.out)

    def test_symlink_output_rejected(self):
        self.out.symlink_to(self.ota)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            bacon.create(self.ota, self.out)

    def test_invalid_name_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Invalid PE ZIP'):
            bacon.create(self.ota, self.root / 'random.zip')

    def test_source_equals_target_rejected(self):
        fake_ota(self.out)
        with self.assertRaisesRegex(ValueError, 'same file'):
            bacon.create(self.out, self.out)

    def test_no_partial_output_if_source_corrupt(self):
        self.ota.write_bytes(b'not a zip')
        with self.assertRaises(ValueError):
            bacon.create(self.ota, self.out)
        self.assertFalse(self.out.exists())

    def test_sidecar_symlink_rejected(self):
        sha = self.out.with_name(self.out.name+'.sha256sum')
        sha.symlink_to(self.ota)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            bacon.create(self.ota, self.out)
        self.assertFalse(self.out.exists())

    def test_make_bacon_with_fake_otapackage(self):
        # Stand-in for AOSP's otapackage target. This is not Soong/bootstrap.
        build_root = self.root / 'buildroot'
        (build_root / 'vendor/aosp/tools').mkdir(parents=True)
        (build_root / 'vendor/aosp/build/tasks').mkdir(parents=True)
        import shutil
        shutil.copy2(ROOT / 'tools/a17_bacon_package.py', build_root / 'vendor/aosp/tools')
        shutil.copy2(ROOT / 'build/tasks/bacon.mk', build_root / 'vendor/aosp/build/tasks')
        mk = build_root / 'Makefile'
        mk.write_text('PRODUCT_OUT := '+str(self.root)+'\n'
                      'CUSTOM_VERSION := PixelExperience_mondrian-17.0-TEST-BETA\n'
                      'INTERNAL_OTA_PACKAGE_TARGET := '+str(self.ota)+'\n'
                      '.PHONY: otapackage\n'
                      'otapackage: '+str(self.ota)+'\n'
                      'include vendor/aosp/build/tasks/bacon.mk\n', encoding='utf-8')
        p = subprocess.run(['make','-f',str(mk),'bacon'],cwd=build_root,
                           stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        self.assertEqual(p.returncode,0,p.stdout+'\n'+p.stderr)
        self.assertEqual(self.out.read_bytes(),self.ota.read_bytes())

    def test_make_refuses_unavailable_aosp_target(self):
        build_root=self.root / 'nomake'
        (build_root / 'vendor/aosp/build/tasks').mkdir(parents=True)
        import shutil
        shutil.copy2(ROOT / 'build/tasks/bacon.mk',build_root/'vendor/aosp/build/tasks')
        (build_root/'Makefile').write_text('PRODUCT_OUT := '+str(self.root)+'\n'
                   'CUSTOM_VERSION := PixelExperience_mondrian-17.0-TEST-BETA\n'
                   'include vendor/aosp/build/tasks/bacon.mk\n')
        p=subprocess.run(['make','bacon'],cwd=build_root,capture_output=True,text=True)
        self.assertNotEqual(p.returncode,0)
        self.assertIn('otapackage',p.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
