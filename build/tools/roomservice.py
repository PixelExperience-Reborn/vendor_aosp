#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""PE-Reborn Android 17: auditable, read-only mondrian roomservice.

Historical roomservice fetched arbitrary devices and recursively synchronized untrusted
repositories. This constrained replacement does not download or modify anything.
Device sources are supplied separately via the maintainer's local manifest.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree

PLATFORM_BRANCH = "seventeen"  # Informational only; never apply to device trees.
DEVICE = "mondrian"
DEVICE_PATH = "device/xiaomi/mondrian"
DEPENDENCY_FILE = "aosp.dependencies"
ALLOWED_DEPENDENCY_PATHS = frozenset({
    "device/xiaomi/sm8450-common",
    "vendor/xiaomi/mondrian",
    "vendor/xiaomi/sm8450-common",
    "kernel/xiaomi/sm8450",
    "kernel/xiaomi/sm8450-modules",
    "kernel/xiaomi/sm8450-devicetrees",
})
REPO_PATTERN = re.compile(r"LF52406/[A-Za-z0-9_.-]+\Z")
REVISION_PATTERN = re.compile(r"[A-Za-z0-9_.\-/]+\Z")
PRODUCT_PATTERN = re.compile(r"(?:aosp_)?mondrian(?:-[A-Za-z0-9_]+-(?:user|userdebug|eng))?\Z")


class RoomserviceError(Exception):
    """A validation failure; no operations have been performed."""


def validate_product(product: str) -> None:
    if not PRODUCT_PATTERN.fullmatch(product):
        raise RoomserviceError(
            "Only mondrian is supported. Expected mondrian, aosp_mondrian or "
            "aosp_mondrian-RELEASE-VARIANT; other devices are blocked."
        )


def load_local_manifest_paths(root: Path) -> set[str]:
    """Read local manifest project paths, never follow or write project sources."""
    result: set[str] = set()
    directory = root / ".repo" / "local_manifests"
    if not directory.exists():
        return result
    if not directory.is_dir():
        raise RoomserviceError(".repo/local_manifests is not a directory")
    for file in sorted(directory.glob("*.xml")):
        if file.is_symlink():
            raise RoomserviceError(f"Symlinked local manifest is not accepted: {file.name}")
        try:
            manifest = ElementTree.parse(file).getroot()
        except (OSError, ElementTree.ParseError) as exc:
            raise RoomserviceError(f"Invalid local manifest {file.name}: {exc}") from exc
        if manifest.tag != "manifest":
            raise RoomserviceError(f"Unexpected XML root in {file.name}")
        for project in manifest.findall("project"):
            path = project.get("path") or project.get("name")
            if path:
                result.add(path)
    return result


def load_dependencies(root: Path) -> tuple[list[dict[str, str]], list[str]]:
    """Validate declaration data as untrusted text, without syncing or changing XML."""
    depfile = root / DEVICE_PATH / DEPENDENCY_FILE
    if not depfile.is_file():
        return [], []
    if depfile.is_symlink():
        raise RoomserviceError("Symlinked aosp.dependencies is not accepted")
    try:
        data = json.loads(depfile.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RoomserviceError(f"Cannot parse {DEVICE_PATH}/{DEPENDENCY_FILE}: {exc}") from exc
    if not isinstance(data, list):
        raise RoomserviceError("aosp.dependencies must be a JSON array")
    validated = []
    blocked = []
    seen = set()
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            blocked.append(f"entry {i}: expected object")
            continue
        repo, path, rev = item.get("repository"), item.get("target_path"), item.get("branch")
        if not isinstance(path, str) or path not in ALLOWED_DEPENDENCY_PATHS:
            blocked.append(f"entry {i}: target_path not approved for mondrian")
            continue
        if not isinstance(repo, str) or not REPO_PATTERN.fullmatch(repo):
            blocked.append(f"entry {i}: repository must be an explicitly reviewed LF52406 fork")
            continue
        if not isinstance(rev, str) or not REVISION_PATTERN.fullmatch(rev) or rev.startswith(("/", "-")) or ".." in rev:
            blocked.append(f"entry {i}: explicit, valid branch is required; never assume seventeen for device trees")
            continue
        if path in seen:
            blocked.append(f"entry {i}: duplicate dependency target_path")
            continue
        seen.add(path)
        validated.append({"repository": repo, "target_path": path, "branch": rev})
    return validated, blocked


def audit(root: Path, product: str, deps_only: bool) -> tuple[dict, int]:
    validate_product(product)
    root = root.resolve()
    if not (root / ".repo").is_dir():
        raise RoomserviceError("Run from a repo checkout root containing .repo, not from Termux home")
    paths = load_local_manifest_paths(root)
    tree_present = (root / DEVICE_PATH).is_dir()
    declared = DEVICE_PATH in paths
    result = {
        "device": DEVICE,
        "platform_branch": PLATFORM_BRANCH,
        "device_path": DEVICE_PATH,
        "device_tree_present": tree_present,
        "local_manifest_declares_tree": declared,
        "dependencies_only": deps_only,
        "dependencies": [],
        "blocked_dependencies": [],
        "read_only": True,
        "auto_discovery": False,
        "auto_sync": False,
    }
    if not tree_present:
        result["status"] = "missing-device-tree"
        result["message"] = (
            "mondrian tree is not checked out. Add its reviewed source to a LOCAL "
            "manifest explicitly, then repo sync that path yourself. No other device trees "
            "or unverified branches are selected automatically."
        )
        return result, 2
    deps, blocked = load_dependencies(root)
    result["dependencies"] = deps
    result["blocked_dependencies"] = blocked
    if blocked:
        result["status"] = "dependencies-require-review"
        result["message"] = "Unapproved or invalid dependencies detected; no sync or manifest edit performed."
        return result, 3
    result["status"] = "inspected"
    result["message"] = (
        "Source tree inspected. Dependencies are informational only; check Android 17 "
        "compatibility before adding or syncing any of them."
    )
    return result, 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only, mondrian-only PE roomservice for AOSP 17")
    parser.add_argument("product", help="mondrian, aosp_mondrian or aosp_mondrian-RELEASE-VARIANT")
    parser.add_argument("legacy_deps", nargs="?", choices=["true", "1"], help="legacy dependencies-only mode")
    parser.add_argument("--deps-only", action="store_true", help="inspect dependencies without modifying source")
    parser.add_argument("--json", action="store_true", help="output machine-readable audit")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="checkout root (testing/debugging)")
    args = parser.parse_args(argv)
    try:
        report, code = audit(args.root, args.product, args.deps_only or bool(args.legacy_deps))
    except RoomserviceError as exc:
        print(f"ROOMSERVICE BLOCKED: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"PE roomservice A17 [{report['device']}]: {report['status']}")
        print(report["message"])
        print(f"Local manifest: {'present' if report['local_manifest_declares_tree'] else 'no device entry'}")
        print(f"Dependencies: {len(report['dependencies'])} validated, {len(report['blocked_dependencies'])} blocked")
        for dep in report["dependencies"]:
            print(f"  REVIEW: {dep['target_path']} <- {dep['repository']} @ {dep['branch']}")
        for warning in report["blocked_dependencies"]:
            print(f"  BLOCKED: {warning}")
        print("No network requests, repo sync, or manifest writes were performed.")
    return code


if __name__ == "__main__":
    sys.exit(main())
