# PixelExperience-Reborn — Android 17 AVB and OTA stage 10

**Draft only. Not a release sign-off.** This change is deliberately limited to signing-key configuration validation and a read-only OTA/target-files metadata preflight. There are no private keys, vendor images, bootloader patches, or flashing commands.

## Verified original PE sources

- `vendor/aosp/config/BoardConfig.mk` includes `config/BoardConfigAvb.mk` only for `CUSTOM_BUILD_TYPE=OFFICIAL` or `CI` if `TARGET_USES_CUSTOM_AVB_KEY=true`.
- The old `BoardConfigAvb.mk` silently set `BOARD_AVB_ALGORITHM := SHA256_RSA2048` and used `external/avb-keys/avb.pem`, while overwriting non-empty recovery/vbmeta_system key paths.
- `vendor/aosp/build/tasks/bacon.mk` depends on `$(INTERNAL_OTA_PACKAGE_TARGET)` and hardlinks the resulting OTA to a PixelExperience-named ZIP. This does **not** sign a target-files package and has not been validated on AOSP 17.
- `config/ota.mk` references an `Updates` app; it is commented out in the inherited `config/common.mk`. A working OTA client/backend has not been established.

## Device review blocker: mondrian / sm8450

In `LF52406/mondrian_android_device_xiaomi_sm8450-common` branch `lineage-24.0`, `BoardConfigCommon.mk` currently sets `BOARD_AVB_ENABLE := true` but uses public AVB test keys and adds `BOARD_AVB_MAKE_VBMETA_IMAGE_ARGS += --flags 3`. These flags disable hashtree and verification. That may be intentional for development; **it must never be described as a verified production chain**. Do not blindly strip those flags from a shipping/test device without considering the OEM bootloader, key trust roots, rollback indexes and recovery path.

## Changes in this stage

1. Replace implicit PE AVB key overrides with strict opt-in validation. The maintainer must explicitly configure `BOARD_AVB_KEY_PATH`, `BOARD_AVB_ALGORITHM`, and required per-partition keys in device-specific configuration. When opt-in is enabled, fail on missing test-key paths, missing key files or disabled-verification flags. This checks configuration, not cryptography.
2. Add `tools/a17_release_preflight.py` to inspect `META/misc_info.txt`, partition list and OTA ZIP entries when real artifacts exist. It never opens private keys, rewrites ZIPs or claims a valid AVB trust chain.
3. Include hermetic Make/ZIP fixture tests. No edits to `bacon.mk`, `ota.mk`, AOSP releasetools, bootloader or update_engine.

## Pending for a real Android 17 release

- Port and build all relevant AOSP 17 source repositories, including `build`, `build_soong`, `update_engine`, `system/sepolicy` and mondrian-specific trees.
- Determine product `AB_OTA_PARTITIONS`, virtual A/B format, dynamic partitions and payload metadata from the actual A17 target-files.
- Confirm the device's AVB key-root arrangement, vbmeta and chained partitions, rollback indexes, installed key compatibility and release-key custody.
- Generate a release-signed target-files ZIP using supported AOSP `sign_target_files_apks` key remapping, then create the OTA with `ota_from_target_files`. Ensure signatures, certificates and OTA payload key match expectations. Never sign on a shared/public build server using exposed production private keys.
- Verify via appropriate cryptographic tools and perform an actual upgrade/downgrade test on an unlockable non-critical device, including data persistence, boot and rollback protections. Nothing in this stage authorizes flashing.

Official docs: https://source.android.com/docs/core/ota/sign_builds and https://source.android.com/docs/security/features/verifiedboot/avb
