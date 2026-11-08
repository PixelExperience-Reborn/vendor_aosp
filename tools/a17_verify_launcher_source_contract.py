#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Qualify the exact Google AOSP17 Launcher3 Quickstep source, without forking.

Requires a REAL targeted checkout from the independent PE-Reborn
aosp17_reference.xml manifest. Git/Soong/XML source assertions only;
does not compile an APK, resolve overlays/permissions on target or boot.
"""
import argparse
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

SOURCE_TAG_COMMIT = "c612e6ece389f21c40f8cb9cd9a4b44239f00009"
GOOGLE_PROJECT = "platform/packages/apps/Launcher3"
AOSP_TAG = "refs/tags/android-17.0.0_r1"
ANDROID = "{http://schemas.android.com/apk/res/android}"


def find_module(src, typ, name):
    matches = re.finditer(r"(?m)^\s*" + re.escape(typ) + r"\s*\{", src)
    for m in matches:
        start = src.index("{", m.start())
        depth = 0
        in_string = False
        escape = False
        for end in range(start, len(src)):
            c = src[end]
            if in_string:
                if escape:
                    escape = False
                elif c == "\\":
                    escape = True
                elif c == '"':
                    in_string = False
            elif c == '"':
                in_string = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    block = src[m.start():end + 1]
                    if re.search(r'\bname:\s*"' + re.escape(name) + r'"', block):
                        return block
                    break
    raise AssertionError(f"missing module: {typ} {name}")


def assert_list_contains(block, field, expected):
    found = re.search(r'\b' + re.escape(field) + r'\s*:\s*\[([^\]]+)\]',
                      block, re.S)
    if not found:
        raise AssertionError(f"{field} list missing")
    names = re.findall(r'"([^"]+)"', found.group(1))
    for name in expected:
        if name not in names:
            raise AssertionError(f"{name} missing from {field}: {names}")


def verify(repo_root, manifest_path):
    repo_root = Path(repo_root)
    manifest_path = Path(manifest_path)
    parsed = ET.parse(manifest_path).getroot()
    defaults = parsed.find("default")
    if defaults is None or defaults.get("revision") != AOSP_TAG:
        raise AssertionError("the AOSP17 reference must be pinned to android-17.0.0_r1")
    names = {p.get("path"): p.get("name") for p in parsed.iter("project")}
    if names.get("packages/apps/Launcher3") != GOOGLE_PROJECT:
        raise AssertionError("Launcher3 must be the official platform source")

    launcher_root = repo_root / "packages/apps/Launcher3"
    checked = subprocess.run(
        ["git", "-C", str(launcher_root), "rev-parse", "HEAD"],
        capture_output=True, check=True, text=True,
    ).stdout.strip()
    if checked != SOURCE_TAG_COMMIT:
        raise AssertionError("Launcher3 AOSP17 source SHA unexpected: " + checked)

    bp = (launcher_root / "Android.bp").read_text(encoding="utf-8")
    base = find_module(bp, "android_app", "Launcher3")
    quickstep = find_module(bp, "android_app", "Launcher3QuickStep")
    if 'system_ext_specific: true' not in base:
        raise AssertionError("AOSP17 Launcher3 partition contract changed")
    for token in ("platform_apis: true", "system_ext_specific: true",
                  "privileged: true"):
        if token not in quickstep:
            raise AssertionError("AOSP17 Quickstep missing " + token)
    assert_list_contains(quickstep, "required",
                         ["privapp_whitelist_com.android.launcher3",
                          "launcher.quickstep.protolog.pb"])
    assert_list_contains(quickstep, "overrides",
                         ["Home", "Launcher2", "Launcher3"])
    assert_list_contains(quickstep, "additional_manifests",
                         ["quickstep/AndroidManifest-launcher.xml",
                          "AndroidManifest-common.xml"])

    xml = ET.parse(launcher_root / "quickstep/AndroidManifest-launcher.xml").getroot()
    home = False
    for activity in xml.findall(".//activity"):
        if activity.get(ANDROID + "exported") != "true":
            continue
        for intent in activity.findall("intent-filter"):
            actions = {p.get(ANDROID + "name") for p in intent.findall("action")}
            cats = {p.get(ANDROID + "name") for p in intent.findall("category")}
            if ("android.intent.action.MAIN" in actions
                    and "android.intent.category.HOME" in cats
                    and "android.intent.category.DEFAULT" in cats):
                home = True
    if not home:
        raise AssertionError("Quickstep HOME/MAIN/DEFAULT exported activity missing")
    common = ET.parse(launcher_root / "AndroidManifest-common.xml").getroot()
    if common.get("package") != "com.android.launcher3":
        raise AssertionError("unexpected launcher package identity")

    print("PASS: official Android17 Launcher3 owner and exact source commit pinned")
    print("PASS: Quickstep privileged system_ext Soong module + required dependencies")
    print("PASS: merged manifest contains exported MAIN/HOME/DEFAULT")
    print("NOTE: this does not build or run Launcher3, validate HOME resolution or Recents")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", required=True)
    parser.add_argument("--reference-manifest", required=True)
    args = parser.parse_args()
    verify(args.checkout, args.reference_manifest)
