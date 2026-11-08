# PixelExperience-Reborn Android 17 — product component migration ledger

**Date:** 2026-11-04. **Scope:** `vendor/aosp` only. **Status:** staged port in Draft PR #1; **not build-ready**.

## Architectural contract

The objective is a **full, independently maintained PixelExperience-Reborn Android 17 platform**, informed by PixelExperience's historical implementation and informed selectively by other Android codebases. Do not rebrand minimal stock AOSP as a finished PixelExperience. Conversely, do not activate Android 14 PE code by default merely because a module is present in the old product makefiles.

The existing `config/common.mk` and related PE product files **remain the migration source of truth for feature inventory**. Their old entries must be evaluated against Android 17 API/module ownership, licensing, compatibility, performance and security. The new `config/a17_base.mk` is **only an optional smoke-test/bootstrap fragment** for PE branding and licensed GMS isolation; it is NOT a replacement for `common.mk` and is not the future complete product definition.

## Audited state of historical PE product components

| Historical PE component | Current migration decision | Required evidence before normal activation |
| --- | --- | --- |
| PE version metadata / branding | Preserved and adapted in `branding.mk` and `main_version.mk` | Test AOSP17 Make product inheritance and platform release config |
| `breakfast` / `brunch` | Ported helper scripts using native AOSP17 `source_vendorsetup()`, no old device listing | Full AOSP17 `lunch`, `m bacon` and product build |
| PE bacon OTA adapter / AVB release guards | Staged, independently tested with synthetic artifacts; no signature bypass | Official release build, target-files, keys, signed OTA and update_engine tests |
| PE sounds / boot animation / font customizations | Preserved in `audio.mk`, `bootanimation.mk`, `fonts.mk` and the PE common product. The font XML stray marker and self-alias loops were fixed; host parsing/source-reference tests PASS | Check module existence, asset licenses (especially bundled Google Sans), font rendering and partition packaging on Android17 |
| AOSP privilege enforcement | Keep `ro.control_privapp_permissions=enforce` | Manifest and permission allowlists of actual apps |
| Google-specific properties, GMS | `WITH_GMS=true` only with separately supplied licensed source | Product build and permission/privileged Google component audit |
| Official AOSP17 `Launcher3QuickStep` HOME / Recents | `config/common.mk` now explicitly selects `PRODUCT_PACKAGES += Launcher3QuickStep` in the real PE common/full/phone product, independent of GMS. The source remains official `platform/packages/apps/Launcher3` pinned via `android-17.0.0_r1`; no 2018 Launcher3 fork or Google APK is copied. | SHA-pinned launcher source and HOME/Soong checks, full `m Launcher3QuickStep` target compilation, installed privileged permission protolog module, Recents/navigation and actual HOME role on Android image. [Source/GMS contract](ANDROID_17_LAUNCHER_GMS_SOURCE_CONTRACT.md) |
| `SystemUIGoogle`, `SettingsGoogle`, `NexusLauncherRelease` and `vendor/pixel-framework` | Historical code preserved; **never automatically replace Android17 SystemUI/Settings**. Google APK dexpreopt requires both `WITH_GMS=true` and `PE_A17_PORT_GOOGLE_PRIV_APPS=true`. Historical `vendor/pixel-framework/config.mk` is no longer silently included from `common.mk`. | Source rights, signing, security, overlays, framework API and device behavior |
| `TouchGestures` | Preserved in `common.mk`, requires `PE_A17_PORT_TOUCH_GESTURES=true` | New event APIs, keyguard/proximity and Soong/source build |
| `Aperture` | Preserved as opt-in `PE_A17_PORT_APERTURE=true`. Official AOSP17 Camera2 remains the source choice for baseline. | CameraX, manifest ownership, dependency/Soong and runtime validation |
| `FaceUnlockService` | Preserved, not advertised from generic base. Requires both `PE_A17_PORT_FACE_UNLOCK=true` and `TARGET_FACE_UNLOCK_SUPPORTED=true`. Default face support is false. | Biometric trust boundary, HAL and lockscreen integration, API, permission, real hardware |
| Legacy PE RRO and static overlays | Files untouched, `PE_A17_PORT_LEGACY_OVERLAYS=true` required to import original group. Google-specific RROs must be reviewed individually before adopting group | Target packages, overlays resource maps, signed APK ownership, density/UI tests |
| Lineage Health permissions | Preserved, now conditional `PE_A17_PORT_LINEAGE_HEALTH_PERMISSIONS=true` | Actual HAL package owner, VINTF instance, application grants; **not** general platform inheritance |
| Qualcomm Protobuf vendorcompat | Preserved, conditional `PE_A17_PORT_QCOM_VENDORCOMPAT=true` | Prove vendor binary consumes these ABIs and modules build on AOSP17; never force QCOM into generic base |
| Legacy `ro.boot.vendor.overlay.theme` assignment | Removed from generic product properties | Android17-compatible navigation mode overlay/Settings selection |
| `persist.sys.disable_rescue=true`, ADB auth and USB override | Removed from `common.mk`; retain native AOSP17 safety policy | Explicit product/security assessment only if a real regression requires a change |
| Legacy NTFS, standalone TextClassifier models and charger images | Original PE modules are **preserved but guarded** by `PE_A17_PORT_NTFS`, `PE_A17_PORT_LEGACY_TEXTCLASSIFIER`, and `PE_A17_PORT_LEGACY_CHARGER`. The default relies on official AOSP17 storage/ExtServices/charger components. `mke2fs` remains selected and QuickAccessWallet is in the official manifest | For each opt-in, prove the actual Android17 module is present and compatible with consumers/partitions; test runtime and OTA |
| OTA updater init and `ota.mk` | Historical code retained; both are now jointly gated behind `PE_A17_PORT_UPDATER=true` and `CUSTOM_BUILD_TYPE=OFFICIAL/CI` instead of unconditionally creating an updater directory | New PE updater module ownership, signed update flow, SELinux and A/B OTA |

### Important limitations

- A `PE_A17_PORT_*=true` flag only restores a **historical module selection**, not compatibility. None of these optional legacy targets is declared successfully ported by that flag. Do not enable one in a release configuration without its corresponding code/API, licensing and platform build proof.
- The original `config/rro_overlays.mk` remains intact for migration review, not an approved list of modern overlays. GMS-only configurations must not be conflated with base AOSP17.
- `common_full.mk`, `common_full_phone.mk` and `common_full_tablet_wifionly.mk` still inherit the PE common product; their real AOSP17 product/target evaluation is pending. `BoardConfig.mk` has been adapted: legacy kernel helpers and Soong namespaces are opt-in, Qualcomm selection fails immediately if its actual source is missing, and existing custom AVB release-key validation is retained. Host Make regression tests cover these boundaries. This does not import device trees.
- This is a **base-platform port**. Do not start or alter mondrian device trees until the platform graph, product build and generic AOSP17 tests are ready.

## Android17-specific follow-up — 4 November 2026

- `config/common.mk` retains the historical PE product's structural sections and branding while removing obsolete ADB/Rescue Party and Dalvik tuning overrides. System properties use `PRODUCT_SYSTEM_PROPERTIES`; Google legal/GMS product keys no longer have duplicate unconditional assignments.
- Old PE `charger_res_images`, NTFS tools, standalone TextClassifier model names, updater init and `Updates` are no longer compulsory on AOSP17. Their source configuration is retained with explicit port flags, while the official AOSP17 ExtServices, storage and charger paths remain the default. This is an integration decision, not evidence that old features have already been successfully reimplemented.
- `BoardConfig.mk` no longer forces the historical `BoardConfigKernel.mk` or a nonexistent Qualcomm/fwk-detect namespace into a generic AOSP17 build; it requires a real source path for explicit Qualcomm opt-in and retains release AVB fail-fast checks.
- PE font customization XML is now statically validated for stray family text, self-aliases, missing family references and missing module names. Open/AOSP Google Font repositories appear in the official manifest; proprietary bundled Google Sans font redistribution is **not automatically authorized by this check**.
- The original `fonts.mk`, `audio.mk`, `bootanimation.mk`, `rro_overlays.mk`, `BoardConfigKernel.mk`, and legacy app/overlay sources remain available in the migration inventory.
- [Vendor host CI #41861159069](https://github.com/PixelExperience-Reborn/vendor_aosp/actions/runs/41861159069) **PASS** verifies Make defaults/port-gates, BoardConfig failure behavior, licensed-GMS isolation, font XML and PE release helper tests. This **does not** prove native Soong module resolution, compilation, OTA acceptance, GMS licensing or device runtime.

## Verification ledger

- [Vendor Make/feature gating CI #41858573264](https://github.com/PixelExperience-Reborn/vendor_aosp/actions/runs/41858573264) — **PASS** on `4d6087c61907c317de8c3d714f8d3317f320f44c`. Tests include old feature retention and explicit package-selection flags. This is host GNU Make + Python/Bash testing, **not** an Android17 target build.
- Source and product change: `config/common.mk` commit `6e9e55b6ec2b4310facee60669c755e4915ca8fe`. The archived `seventeen` branch remains unchanged.
- Source graph: manifest's opt-in profile pins `vendor_aosp` and verified platform projects; the historical `default.xml` is not the production checkout path.

**Remaining acceptance gate:** resolve a real generic Android17 PE product in Soong/Make, check actual modules and feature compatibility (including QuickAccessWallet, GMS/Fonts/RRO, updated charger/NTFS/TextClassifier and release integration), complete selected-source Android17 compilation and security tests, then later perform independent device-tree bring-up. Host-unit completion must not be mistaken for a shippable ROM.
