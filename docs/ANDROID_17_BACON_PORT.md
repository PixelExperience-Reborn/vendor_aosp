# PixelExperience-Reborn A17 `bacon` — stage 11

**Draft, not verified on a synced Android 17 tree.** Do not merge/flash based on this stage alone.

## Audited sources

- Original PE `vendor_aosp/build/tasks/bacon.mk` made a `$(CUSTOM_VERSION).zip` hard link of `$(INTERNAL_OTA_PACKAGE_TARGET)` and created a SHA-256 file using `prebuilts/build-tools/path/$(HOST_PREBUILT_TAG)/sha256sum`.
- AOSP 17 tag `android-17.0.0_r1`, `build/make/core/Makefile`, still declares `INTERNAL_OTA_PACKAGE_TARGET` and `otapackage` **under** `ifeq ($(build_ota_package),true)`. The OTA rule depends on `$(BUILT_TARGET_FILES_DIR)` and calls AOSP `$(OTA_FROM_TARGET_FILES)` with its own signing key.
- `bacon.mk` exists under vendor but inclusion into the Android 17 Kati graph **has not been established**. The stage does not patch the AOSP `build/make` core or force-load any Makefile.

## Changes

- `bacon: otapackage` delegates OTA production to AOSP, and then runs a packaging helper with the produced `INTERNAL_OTA_PACKAGE_TARGET`. If AOSP has no OTA rule, the target is supposed to fail instead of inventing an unsigned archive.
- The helper requires a valid-looking A/B (`payload.bin` + `payload_properties.txt`) or recovery (`META-INF/com/google/android/update-binary`) ZIP, copies its bytes without modification, and writes `<PixelExperience_...>.zip.sha256sum`.
- Existing ZIP with a *different* content digest is never overwritten. Same-content reruns are idempotent. Output names are restricted to `PixelExperience_*.zip`.
- Does **not** generate, validate or rotate keys, create OTA payloads, invoke `sign_target_files_apks`, or assert that an OTA is installable.

## Still blocked

1. Confirm AOSP17 Build port loads `vendor/aosp/build/tasks/bacon.mk` at the proper stage and `build_ota_package=true` when building `bacon`; no naive include from `core/main.mk` before AOSP defines the OTA target.
2. On a Linux host, use a complete `repo sync` at pinned AOSP17 revisions. Inspect with `m --dry-run bacon` or equivalent Kati/ninja graph and `m otapackage`; run a real `m bacon` only after integration is reviewed.
3. Build `target-files` and verify their `META/misc_info.txt`, AB/Virtual A/B partitions, dynamic partition metadata, signing identities, rollback indices and installed update_engine.
4. Sign `target-files` with protected keys using AOSP releasetools and regenerate OTA from the signed target-files. Verify the resulting ZIP's package signature separately. SHA-256 checks **integrity only**, not authenticity.
5. For mondrian, review its current `BOARD_AVB_MAKE_VBMETA_IMAGE_ARGS += --flags 3` and test AVB/rollback/OTA behavior on the device; the generic PE task must not modify that device tree.

## Offline validation

`python3 tests/a17_bacon_package_test.py` exercises ZIP byte equality, SHA-256, rerun, collision and symlink refusal, missing target, and a synthetic `make bacon` with a mocked AOSP `otapackage`. **It is not a real OTA build.**

## Termux compatibility fix

Android Termux Python builds may not expose `os.link`. The packaging tool
uses exclusive destination creation (`O_CREAT|O_EXCL`) after verifying a
temporary copy, with a second SHA-256 verification and cleanup on handled
errors. It will not overwrite an existing ZIP. Unlike a hard-link, the
destination can be momentarily visible while copying; the sidecar is written
only after the copy is finished. Do not distribute an output ZIP until the
packaging command has completed successfully. This is not an OTA security
verification or a release sign-off.
