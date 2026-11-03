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

## Remaining work

- Audit `ro.com.google.clientidbase`, Google atrace/error receiver, OPA, proprietary package references and launcher overlays: some legacy properties are still assigned by `common.mk` in non-GMS mode.
- Test both choices against the *full* AOSP17 product dependency graph. Default includes for old PixelExperience do not guarantee a functioning pure AOSP product.
- Validate proprietary licensing/privapp permissions and CTS/GMS constraints for a release.
- Maintain GMS selection as an explicit build configuration; do not silently inject proprietary or unknown prebuilts.

This change belongs in the staged [vendor_aosp PR #1](https://github.com/PixelExperience-Reborn/vendor_aosp/pull/1). Keep `seventeen` unchanged until proper validation.
