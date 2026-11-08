# PixelExperience-Reborn Android 17: version metadata audit (stage 9)

**Draft only: not integrated or built on Android 17.** This stage makes a deliberately limited migration inside the existing `vendor_aosp` draft PR #1.

## Audited original code

- `config/branding.mk` hard-coded ROM version `14.0`, branch `fourteen` and produced independent UTC timestamps.
- `build/core/main_version.mk` built its own `BUILD_FINGERPRINT`, guessed `release-keys` based on `CUSTOM_BUILD_TYPE`, duplicated `ro.build.fingerprint`, and hard-coded `CUSTOM_SECURITY_PATCH := 2022-08-05`.
- `config/common.mk` forced `PRODUCT_BUILD_PROP_OVERRIDES += BUILD_UTC_DATE=0` and includes `config/branding.mk` using `inherit-product`.
- `config/BoardConfigAvb.mk` points at `external/avb-keys/avb.pem` when separately enabled; key provisioning and release signing are **unverified**, not modified here.
- `config/ota.mk` references the `Updates` app but is commented out in `common.mk`. `build/tasks/bacon.mk` uses `INTERNAL_OTA_PACKAGE_TARGET`. Neither OTA backend nor updater compatibility with AOSP 17 is verified.

## Patch scope

1. `config/branding.mk`: retain `PixelExperience_...` filename identity and `org.pixelexperience.*` metadata, update ROM label to 17.0 / seventeen, derive the displayed date and epoch from one UTC source, optionally `SOURCE_DATE_EPOCH`, and use `PRODUCT_SYSTEM_PROPERTIES` (through the existing `common.mk` inheritance).
2. Emit custom `org.pixelexperience.build_security_patch` **only if** AOSP `PLATFORM_SECURITY_PATCH` is defined in the product context. If it isn't, omit the optional PE alias, never invent a patch date. The canonical security level is AOSP's `ro.build.version.security_patch`.
3. `build/core/main_version.mk`: retain a compatibility *no-op*; no overriding Android's fingerprint/build identity, signing tags, platform patch, or timestamps from this historical Makefile.
4. `config/common.mk`: remove only `BUILD_UTC_DATE=0`, allowing normal AOSP 17 build timestamp handling.
5. Add make-based local tests. They validate metadata generation and prohibited legacy overrides; **they do not demonstrate complete product integration, actual signing, image properties or OTA success**.

## Important follow-up gates

- Inspect `CUSTOM_BUILD`, `CUSTOM_BUILD_TYPE` and `PRODUCT_SYSTEM_PROPERTIES` on a synced AOSP 17 device product. Confirm that the inherited `branding.mk` is evaluated at the correct stage, and `PLATFORM_SECURITY_PATCH` is populated.
- Preserve actual platform and vendor patch levels separately; never claim an updated vendor/boot patch without matching partition updates.
- Audit Android 17 release signing (`sign_target_files_apks`) and test signing with *private* keys on the build server only. Never commit, copy, or request secrets for this audit. `release-keys` is not a branding switch.
- Audit actual A/B OTA generation and signing. Do not enable `Updates`, the old `bacon` target, updater endpoints or automatically claim OTA support without checking build rules and a successful update test.
- Verify `repo manifest -r`, `repo sync`, Soong bootstrap, target build, generated `system/build.prop` and partition props, AVB chain, first boot, and OTA before merging this draft.

## Explicit non-goals

No new repos, branches, device trees, GMS blobs, signing key changes, AOSP source merges or commits to default `seventeen`.
