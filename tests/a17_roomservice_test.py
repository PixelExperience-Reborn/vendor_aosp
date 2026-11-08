#!/usr/bin/env python3
"""Unit tests for the side-effect-free PE A17 mondrian roomservice."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parents[1] / "build" / "tools" / "roomservice.py"
if not MODULE_PATH.exists():
    MODULE_PATH = Path(__file__).with_name("roomservice.py")
spec = importlib.util.spec_from_file_location("pe_roomservice_a17", MODULE_PATH)
rs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rs)


class RoomserviceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / ".repo" / "local_manifests").mkdir(parents=True)

    def add_tree(self):
        (self.root / "device/xiaomi/mondrian").mkdir(parents=True)

    def deps(self, items):
        self.add_tree()
        (self.root / rs.DEVICE_PATH / "aosp.dependencies").write_text(json.dumps(items), encoding="utf-8")

    def test_missing_tree_no_side_effect(self):
        before = set(self.root.rglob("*"))
        out, code = rs.audit(self.root, "aosp_mondrian", False)
        self.assertEqual((out["status"], code), ("missing-device-tree", 2))
        self.assertEqual(before, set(self.root.rglob("*")))

    def test_valid_tree_no_dependencies(self):
        self.add_tree()
        out, code = rs.audit(self.root, "mondrian", False)
        self.assertEqual(code, 0)
        self.assertEqual(out["dependencies"], [])

    def test_modern_lunch_combo(self):
        self.add_tree()
        self.assertEqual(rs.audit(self.root, "aosp_mondrian-trunk_staging-userdebug", False)[1], 0)

    def test_other_device_rejected(self):
        with self.assertRaises(rs.RoomserviceError):
            rs.audit(self.root, "aosp_raphael", False)

    def test_injection_rejected(self):
        with self.assertRaises(rs.RoomserviceError):
            rs.audit(self.root, "mondrian;echo BAD", False)

    def test_dependencies_validated_without_sync(self):
        self.deps([{"repository":"LF52406/mondrian_android_device_xiaomi_sm8450-common", "target_path":"device/xiaomi/sm8450-common", "branch":"lineage-24.0"}])
        before = sorted(str(p) for p in self.root.rglob("*"))
        with mock.patch.object(rs, "load_local_manifest_paths", wraps=rs.load_local_manifest_paths):
            out, code = rs.audit(self.root, "mondrian", True)
        self.assertEqual(code, 0)
        self.assertEqual(len(out["dependencies"]), 1)
        self.assertEqual(before, sorted(str(p) for p in self.root.rglob("*")))

    def test_other_device_dependency_blocked(self):
        self.deps([{"repository":"LF52406/device_other", "target_path":"device/xiaomi/raphael", "branch":"seventeen"}])
        report, code = rs.audit(self.root, "mondrian", False)
        self.assertEqual(code, 3)
        self.assertEqual(len(report["blocked_dependencies"]), 1)

    def test_external_owner_blocked(self):
        self.deps([{"repository":"UnknownOrg/a", "target_path":"device/xiaomi/sm8450-common", "branch":"seventeen"}])
        self.assertEqual(rs.audit(self.root, "mondrian", False)[1], 3)

    def test_missing_device_revision_blocked(self):
        self.deps([{"repository":"LF52406/a", "target_path":"device/xiaomi/sm8450-common"}])
        self.assertEqual(rs.audit(self.root, "mondrian", False)[1], 3)

    def test_traversal_revision_blocked(self):
        self.deps([{"repository":"LF52406/a", "target_path":"device/xiaomi/sm8450-common", "branch":"../main"}])
        self.assertEqual(rs.audit(self.root, "mondrian", False)[1], 3)

    def test_duplicate_dependency_blocked(self):
        d={"repository":"LF52406/a", "target_path":"device/xiaomi/sm8450-common", "branch":"seventeen"}
        self.deps([d,d])
        self.assertEqual(rs.audit(self.root, "mondrian", False)[1], 3)

    def test_invalid_manifest_rejected(self):
        (self.root / ".repo/local_manifests/broken.xml").write_text("<manifest>")
        self.add_tree()
        with self.assertRaises(rs.RoomserviceError):
            rs.audit(self.root, "mondrian", False)

    def test_manifest_detected(self):
        self.add_tree()
        (self.root / ".repo/local_manifests/device.xml").write_text('<manifest><project name="foo" path="device/xiaomi/mondrian" /></manifest>')
        self.assertTrue(rs.audit(self.root, "mondrian", False)[0]["local_manifest_declares_tree"])

    def test_repo_root_required(self):
        (self.root / ".repo").rename(self.root / "repo_backup")
        with self.assertRaises(rs.RoomserviceError):
            rs.audit(self.root, "mondrian", False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
