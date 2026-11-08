#!/usr/bin/env python3
"""AOSP17 source-ownership gate for PE-Reborn product package references.

Run against a checkout of the pinned AOSP17 manifest with the selected
official upstream projects synced. This checks module/source ownership and
external fonts, not Soong resolution, compilation or redistribution rights.
"""
from pathlib import Path
import re
import sys

VENDOR = Path(__file__).resolve().parents[1]
AOSP = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None
if AOSP is None or not AOSP.is_dir():
    sys.exit("Usage: python3 tools/a17_verify_source_consumers.py /path/to/aosp")

fonts_make = (VENDOR / "config/fonts.mk").read_text(encoding="utf-8")
font_names = set(re.findall(r"\b[A-Za-z0-9_-]+\.ttf\b", fonts_make))
bundled_names = {
    "GoogleSans-Italic.ttf", "GoogleSans-Regular.ttf",
    "GoogleSansClock-Regular.ttf", "GoogleSansFlex-Regular.ttf",
}
missing_bundled = [
    name for name in sorted(bundled_names)
    if not (VENDOR / "fonts" / name).is_file()
]
if missing_bundled:
    sys.exit(f"Missing original PE bundled font modules: {missing_bundled}")

font_repos = (
    "arbutus-slab", "lato", "rubik", "zilla-slab", "lustria",
    "karla", "fraunces", "big-shoulders-text", "barlow",
)
aosp_font_root = AOSP / "external/google-fonts"
font_sources = set()
for repo in font_repos:
    folder = aosp_font_root / repo
    if not folder.is_dir():
        sys.exit(f"Missing pinned official AOSP17 font project: {folder}")
    font_sources.update(f.name for f in folder.rglob("*.ttf"))
missing_fonts = sorted(font_names - bundled_names - font_sources)
if missing_fonts:
    sys.exit(f"Unresolved PE font references in pinned AOSP17 sources: {missing_fonts}")

def source_defines_module(project, module):
    repo_root = AOSP / project
    if not repo_root.is_dir():
        sys.exit(f"Missing official AOSP17 source project: {repo_root}")
    # Only scan module descriptors; names appearing in README/source aren't
    # evidence that a package can be built by Android.
    for pat in ("Android.bp", "Android.mk"):
        for descriptor in repo_root.rglob(pat):
            text = descriptor.read_text(encoding="utf-8", errors="replace")
            if re.search(r'name\s*:\s*["\x27]' + re.escape(module) + r'["\x27]', text):
                return descriptor
            if re.search(r'LOCAL_(?:MODULE|PACKAGE_NAME)\s*:?=\s*' +
                         re.escape(module) + r'(?:\s|$)', text, flags=re.M):
                return descriptor
    sys.exit(f"No exact {module} Android module definition in {project}")

mk = (VENDOR / "config/common.mk").read_text(encoding="utf-8")
for module, project in (
    ("mke2fs", "external/e2fsprogs"),
    ("QuickAccessWallet", "packages/apps/QuickAccessWallet"),
):
    if not re.search(r"(?m)^\s*" + re.escape(module) + r"\s*(?:\\)?$", mk):
        sys.exit(f"Expected PE common product reference vanished: {module}")
    descriptor = source_defines_module(project, module)
    print(f"PASS: {module} defined by {descriptor.relative_to(AOSP)}")

extservices = AOSP / "packages/modules/ExtServices"
if not extservices.is_dir() or not any(extservices.rglob("Android.bp")):
    sys.exit("Missing pinned AOSP17 ExtServices source/module definition")
if "libtextclassifier_annotator_en_model" not in mk:
    sys.exit("Lost historical TextClassifier migration inventory")
if "PE_A17_PORT_LEGACY_TEXTCLASSIFIER" not in mk:
    sys.exit("Old TextClassifier modules are not gated for AOSP17")
print(f"PASS: {len(font_names - bundled_names)} PE font names supplied by pinned AOSP sources")
print("PASS: AOSP17 source owners detected for default wallet/storage and ExtServices")
print("NOT TESTED: Android17 Soong build, runtime, CTS, commercial font licensing")
