# Android 17 GMS selection — PixelExperience-Reborn

**Status:** early AOSP17 product configuration fix. This does **not** establish a fully functional, licensed GMS or GMS-free product image.

## Behavior

`vendor/aosp/config/common.mk` no longer imports `vendor/gms/products/gms.mk` unconditionally.

- **No `WITH_GMS=true`:** the proprietary product makefile is not inherited. This allows an open-source AOSP17 source-only bootstrap to proceed without first obtaining GMS.
- **`WITH_GMS=true`, source missing:** make parsing fails with a descriptive error rather than silently shipping a partial proprietary configuration.
- **`WITH_GMS=true`, source present:** the original `inherit-product` call remains active.

The Google app payload, keys and licensing are not stored or redistributed here. `vendor/gms/products/gms.mk` is *not* one of the 135 PixelExperience-Reborn repositories. The maintainer must obtain and verify an appropriately licensed GMS source independently.

## Validation scope

Three isolated GNU Make fixture scenarios were evaluated: non-GMS selection; explicit GMS selection with missing makefile (expected error); explicit GMS selection with existing makefile (expected import). **No actual Android17 product make parse/build, full package installation or CTS/GMS certification was performed.**

## Native Launcher3 / Quickstep selection on PE common product

The staged **PE common product** now explicitly selects `Launcher3QuickStep` from **official Google AOSP17** in `PRODUCT_PACKAGES`. This open-source HOME/Recents baseline is independent of `WITH_GMS` and remains present for both no-GMS and explicit-GMS product selection. The older PixelExperience Launcher3 GitHub fork is Android 8.1-only and is not imported.

Original PE14 only placed `NexusLauncherRelease` and `SystemUIGoogle` in `PRODUCT_DEXPREOPT_SPEED_APPS`; that is **not** evidence of their `PRODUCT_PACKAGES` inclusion. Proprietary `vendor/gms` came from an external PE GitLab source and exact APK/provider and redistribution rights remain unverified. A real licensed GMS product that installs another HOME/Recents provider must explicitly resolve the competing launcher/Recents/privileged-app contracts before a release. GMS is still optional, not disabled or silently bundled.

[Detailed Android17 Launcher3QuickStep and GMS source contract](ANDROID_17_LAUNCHER_GMS_SOURCE_CONTRACT.md). The new 7-case GNU Make suite checks product package decisions, and the targeted AOSP17 launcher source gate checks the actual SHA, Soong module and HOME manifest. **This is not proof of a compiled Launcher3 APK or a booted product.**

## Remaining work

- The legacy `ro.com.google.clientidbase`, Google error/atrace receivers, legal links, OPA, Gboard and Google SetupWizard properties are now conditional on `WITH_GMS=true`; so is dexpreopt of `SystemUIGoogle` and `NexusLauncherRelease`. The GMS source itself is required only for explicit GMS builds.
- Review additional independent defaults such as `TARGET_SUPPORTS_GOOGLE_RECORDER`, `TARGET_INCLUDE_STOCK_ARCORE`, `NexusLauncherResOverlay` and other packages/overlays. These have **not** been verified for GMS-free builds.
- Test both choices against the *full* AOSP17 product dependency graph. Conditional property selection does not by itself guarantee a functioning pure AOSP product.
- Validate proprietary licensing/privapp permissions and CTS/GMS constraints for a release.
- Maintain GMS selection as an explicit build configuration; do not silently inject proprietary or unknown prebuilts.

This change belongs in the staged [vendor_aosp PR #1](https://github.com/PixelExperience-Reborn/vendor_aosp/pull/1). Keep `seventeen` unchanged until proper validation.
