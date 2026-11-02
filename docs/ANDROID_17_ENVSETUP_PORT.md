# PixelExperience-Reborn: AOSP 17 environment helpers — stage 6

Status: **draft / not build validated**. This migration does not make `vendor_aosp` Android 17 compatible by itself.

## What was actually ported

- `breakfast` and `brunch` in `build/envsetup.sh` are the original PE helper commands with minimal AOSP 17 argument adaptation.
- New `breakfast <device> [variant] [release]` uses `lunch PRODUCT RELEASE VARIANT` without overriding AOSP `lunch` or the release selection logic. Example: `breakfast mondrian userdebug trunk_staging`.
- A full combo such as `breakfast aosp_mondrian-trunk_staging-userdebug` is accepted; the older `breakfast aosp_mondrian-userdebug` is translated for compatibility.
- The fallback `PE_LUNCH_RELEASE` is `trunk_staging`, which **must exist for the actual product**; verify using the AOSP 17 `list_releases` command. Do not silently substitute a release configuration.
- `brunch` preserves the PE `mka bacon` target and now stops on failed `breakfast`. The existence of a working `bacon` make target on Android 17 has **not** been established.

## How the helpers are loaded

`build/envsetup.sh` from the AOSP 17 Build port (separate, unmerged candidate) conditionally sources `vendor/aosp/build/envsetup.sh`. This repository change by itself does **not** alter the AOSP build file or override `lunch`.

## Validation

Run `bash -n vendor/aosp/build/envsetup.sh` and `bash tests/a17_envsetup_helpers_test.sh vendor/aosp/build/envsetup.sh`. Tests mock `lunch` and `mka`; they do not prove that a real product lunch, Soong bootstrap, `mka bacon` or full build works.

## Blockers before the port can be merged

1. Validate official AOSP 17 `lunch` and the `mondrian` product's `AndroidProducts.mk`/release map on a synced Linux checkout.
2. Adapt or retire the outdated `vendorsetup.sh` list of two-part lunch choices; AOSP 17 uses release configurations and product definitions, not that historical array as the source of truth.
3. Audit `roomservice.py`: hardcoded `fourteen` revision, references to the original device organization, and old product detection. Do not run it automatically.
4. Restore the PE `bacon` build target only after checking release packaging and `vendor_aosp` make rules.
5. Review independent PE features: GMS licensing and dependency (`vendor/gms/products/gms.mk`), build fingerprint, signing keys, security patch source, OTA packaging, SELinux, and Qualcomm specifics. Do not copy Android 14 logic blindly.
6. Test with a full Android 17 repo sync, Soong bootstrap, target build and actual device boot before merging to `seventeen`.

## Changes deliberately not made

No device trees, no GMS blobs, no automatic source merges, no changes to `vendorsetup.sh`, `roomservice.py`, `common.mk`, or target signing/version properties. The original PE helper names are retained.

## Stage 7 — AOSP 17 selection / obsolete vendorsetup

- `breakfast` with no arguments no longer calls the removed interactive `lunch` menu. In an interactive terminal it selects a product via AOSP `list_products`, validates release choices with `list_releases`, and then calls AOSP `lunch PRODUCT RELEASE userdebug`. Without an interactive terminal it displays products and exits nonzero; no build starts.
- `breakfast --help` and `brunch --help` are side-effect-free; `brunch` still never builds after a failed selection.
- `vendorsetup.sh` no longer downloads the original PE official_devices/Android 14 list or populates `lunch_others_targets`. Android 17 product discovery belongs in each device's `AndroidProducts.mk` and `build/release`. This change creates **no other device trees**.
- `build/tools/roomservice.py` is deliberately **unchanged**. Its original organization, hardcoded fallback `fourteen`, auto-sync and local-manifest writes must be separately audited before activation. Do not auto-run it on the Android 17 base.
- Tests are shell-mock/static tests only. Interactive selection, product availability, full AOSP 17 lunch, Soong bootstrap and `bacon` need a synced Linux build tree.
- This stage updates the **existing** draft PR #1. No new repo, PR or default-branch change.
