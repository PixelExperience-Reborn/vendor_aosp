#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Isolated GNU Make tests for PE's AOSP17 board integration boundaries.

This test does not emulate AOSP's build system, compile Qualcomm code, or
validate any device tree. It catches accidental unconditional legacy imports.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BoardConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pe-a17-board-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "vendor").mkdir()
        (self.root / "vendor/aosp").symlink_to(ROOT, target_is_directory=True)

    def make(self, **variables):
        lines = [f"{key} := {value}" for key, value in variables.items()]
        lines += [
            "include vendor/aosp/config/BoardConfig.mk",
            "all:",
            "\t@printf '%s\\n' 'QCOM=$(BOARD_USES_QCOM_HARDWARE)' "
            "'NAMESPACES=$(strip $(PRODUCT_SOONG_NAMESPACES))' "
            "'ADAPTER=$(PE_QCOM_STUB_INCLUDED)'",
        ]
        (self.root / "Makefile").write_text("\n".join(lines) + "\n", encoding="utf-8")
        return subprocess.run(
            ["make", "--no-print-directory", "-s", "all"],
            cwd=self.root, capture_output=True, text=True, timeout=20,
            check=False,
        )

    def test_generic_aosp17_no_legacy_or_missing_namespace(self):
        p = self.make()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("NAMESPACES=", p.stdout)
        self.assertNotIn("hardware/qcom-caf/common", p.stdout)
        self.assertNotIn("fwk-detect", p.stdout)

    def test_qcom_requires_its_actual_adapter(self):
        p = self.make(BOARD_USES_QCOM_HARDWARE="true")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("requires a ported Qualcomm BoardConfig", p.stderr)

    def test_qcom_adapter_is_loaded_only_when_real_file_exists(self):
        qcom = self.root / "hardware/qcom-caf/common"
        qcom.mkdir(parents=True)
        (qcom / "BoardConfigQcom.mk").write_text(
            "PE_QCOM_STUB_INCLUDED := true\n", encoding="utf-8",
        )
        p = self.make(BOARD_USES_QCOM_HARDWARE="true")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("ADAPTER=true", p.stdout)

    def test_fwk_detect_requires_explicit_real_namespace(self):
        p = self.make(PE_A17_PORT_FWK_DETECT="true")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("requires TARGET_FWK_DETECT_PATH", p.stderr)
        p = self.make(
            PE_A17_PORT_FWK_DETECT="true",
            TARGET_FWK_DETECT_PATH="hardware/example",
        )
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("fwk-detect/Android.bp missing", p.stderr)
        directory = self.root / "hardware/example/fwk-detect"
        directory.mkdir(parents=True)
        (directory / "Android.bp").write_text("// fixture only\n", encoding="utf-8")
        p = self.make(
            PE_A17_PORT_FWK_DETECT="true",
            TARGET_FWK_DETECT_PATH="hardware/example",
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("NAMESPACES=hardware/example/fwk-detect", p.stdout)

    def test_explicit_release_avb_cannot_omit_signing_key(self):
        p = self.make(
            CUSTOM_BUILD_TYPE="OFFICIAL",
            TARGET_USES_CUSTOM_AVB_KEY="true",
            BOARD_AVB_ENABLE="true",
            BOARD_AVB_ALGORITHM="SHA256_RSA4096",
        )
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("BOARD_AVB_KEY_PATH", p.stderr)

    def test_release_signing_checks_still_reject_public_keys(self):
        p = self.make(
            CUSTOM_BUILD_TYPE="OFFICIAL",
            TARGET_USES_CUSTOM_AVB_KEY="true",
            BOARD_AVB_ENABLE="true",
            BOARD_AVB_ALGORITHM="SHA256_RSA4096",
            BOARD_AVB_KEY_PATH="external/avb/test/data/testkey_rsa2048.pem",
        )
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("public AOSP test key", p.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
