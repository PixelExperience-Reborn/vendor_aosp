# PixelExperience-Reborn: AOSP 17 environment helpers — stage 6

Status: **draft / not build validated**. This migration does not make `vendor_aosp` Android 17 compatible by itself.

## What was actually ported

- `breakfast` and `brunch` in `build/envsetup.sh` are the original PE helper commands with minimal AOSP 17 argument adaptation.
- New `breakfast <device> [variant] [release]` uses `lunch PRODUCT RELEASE VARIANT` without overriding AOSP `lunch` or the release selection logic. Example: `breakfast mondrian userdebug trunk_staging`.
- A full combo such as `breakfast aosp_mondrian-trunk_staging-userdebug` is accepted; the older `breakfast aosp_mondrian-userdebug` is translated for compatibility.
- The fallback `PE_LUNCH_RELEASE` is `trunk_staging`, which **must exist for the actual product**; verify using the AOSP 17 `list_releases` command. Do not silently substitute a release configuration.
- `brunch` preserves the PE `mka bacon` target and now stops on failed `breakfast`. The existence of a working `bacon` make target on Android 17 has **not** been established.

## How the helpers are loaded

**Current stage 15:** The official AOSP17 `build/envsetup.sh` calls `source_vendorsetup()`, which sources `vendor/aosp/vendorsetup.sh` when this PE vendor repository is present in the checkout. That file now loads `vendor/aosp/build/envsetup.sh` after verifying the build root and helper file. **No patch to the AOSP `build/make` source is required for these PE shell helpers**, and the original `lunch` function is preserved. An earlier local `build/make` hook proposal is superseded and is not required for the active bootstrap.

## Validation

Run `bash -n vendor/aosp/vendorsetup.sh`, `bash -n vendor/aosp/build/envsetup.sh`, `bash tests/a17_envsetup_helpers_test.sh vendor/aosp/build/envsetup.sh` and `bash tests/a17_vendorsetup_test.sh vendor/aosp/vendorsetup.sh`. These run in GitHub Actions on the staged PR. The latter test simulates AOSP `source_vendorsetup()` loading PE helpers and confirms `lunch` is untouched. This is not an actual AOSP product lunch, Soong bootstrap, bacon or ROM build.

## Blockers before the port can be merged

1. Validate official AOSP 17 `lunch` and the `mondrian` product's `AndroidProducts.mk`/release map on a synced Linux checkout.
2. **Addressed for the bootstrap:** `vendorsetup.sh` no longer uses old lunch combo discovery; it loads only PE shell helper functions. Full device product/release discovery remains to be validated on AOSP17.
3. Audit `roomservice.py`: hardcoded `fourteen` revision, references to the original device organization, and old product detection. Do not run it automatically.
4. Restore the PE `bacon` build target only after checking release packaging and `vendor_aosp` make rules.
5. Review independent PE features: GMS licensing and dependency (`vendor/gms/products/gms.mk`), build fingerprint, signing keys, security patch source, OTA packaging, SELinux, and Qualcomm specifics. Do not copy Android 14 logic blindly.
6. Test with a full Android 17 repo sync, Soong bootstrap, target build and actual device boot before merging to `seventeen`.

## Changes deliberately not made

Stage 6 originally touched only PE helper definitions. Later stages intentionally changed `vendorsetup.sh`, `roomservice.py`, `common.mk`, version metadata and AVB/OTA preflight in this same draft PR. No other-device tree or GMS blob was added, and the core AOSP build/make source remains untouched. Those later changes remain staged and not build-validated.

## Stage 7 — AOSP 17 selection / obsolete vendorsetup

- `breakfast` with no arguments no longer calls the removed interactive `lunch` menu. In an interactive terminal it selects a product via AOSP `list_products`, validates release choices with `list_releases`, and then calls AOSP `lunch PRODUCT RELEASE userdebug`. Without an interactive terminal it displays products and exits nonzero; no build starts.
- `breakfast --help` and `brunch --help` are side-effect-free; `brunch` still never builds after a failed selection.
- `vendorsetup.sh` no longer downloads the original PE official_devices/Android 14 list or populates `lunch_others_targets`. At stage 15 it additionally loads `vendor/aosp/build/envsetup.sh` through official AOSP17 `source_vendorsetup()`. Android 17 product discovery belongs in each device's `AndroidProducts.mk` and `build/release`. This change creates **no other device trees**.
- `build/tools/roomservice.py` is deliberately **unchanged**. Its original organization, hardcoded fallback `fourteen`, auto-sync and local-manifest writes must be separately audited before activation. Do not auto-run it on the Android 17 base.
- Tests are shell-mock/static tests only. Interactive selection, product availability, full AOSP 17 lunch, Soong bootstrap and `bacon` need a synced Linux build tree.
- This stage updates the **existing** draft PR #1. No new repo, PR or default-branch change.

## Stage 15 — upstream-first shell integration, CI

- GitHub commit `789eee9bb63d` connects PE helper definitions via the existing AOSP17 `source_vendorsetup()` mechanism. Build/make itself stays byte-for-byte AOSP17 in the bootstrap profile.
- Regression tests `a17_envsetup_helpers_test.sh` and `a17_vendorsetup_test.sh` now run on GitHub Actions with read-only contents permission. This tests shell behavior, not compiled Android code.
- No default `seventeen` branch updated. Existing historical PE build/make retains its original commits for future per-change review.
- Further build/make patches are permitted only if supported by a separate concrete Android17 regression, not simply to reproduce an obsolete Android14 environment hook.
