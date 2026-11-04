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
| PE sounds / boot animation / font customizations | Preserved in `audio.mk`, `bootanimation.mk`, `fonts.mk`, legacy `common.mk` references | Verify asset paths, licenses, format, product image paths and product build |
| AOSP privilege enforcement | Keep `ro.control_privapp_permissions=enforce` | Manifest and permission allowlists of actual apps |
| Google-specific properties, GMS | `WITH_GMS=true` only with separately supplied licensed source | Product build and permission/privileged Google component audit |
| `SystemUIGoogle`, `SettingsGoogle`, `NexusLauncherRelease` and `vendor/pixel-framework` | Historical code preserved; **never automatically replace Android17 SystemUI/Settings**. Google APK dexpreopt requires both `WITH_GMS=true` and `PE_A17_PORT_GOOGLE_PRIV_APPS=true`. Historical `vendor/pixel-framework/config.mk` is no longer silently included from `common.mk`. | Source rights, signing, security, overlays, framework API and device behavior |
| `TouchGestures` | Preserved in `common.mk`, requires `PE_A17_PORT_TOUCH_GESTURES=true` | New event APIs, keyguard/proximity and Soong/source build |
| `Aperture` | Preserved as opt-in `PE_A17_PORT_APERTURE=true`. Official AOSP17 Camera2 remains the source choice for baseline. | CameraX, manifest ownership, dependency/Soong and runtime validation |
| `FaceUnlockService` | Preserved, not advertised from generic base. Requires both `PE_A17_PORT_FACE_UNLOCK=true` and `TARGET_FACE_UNLOCK_SUPPORTED=true`. Default face support is false. | Biometric trust boundary, HAL and lockscreen integration, API, permission, real hardware |
| Legacy PE RRO and static overlays | Files untouched, `PE_A17_PORT_LEGACY_OVERLAYS=true` required to import original group. Google-specific RROs must be reviewed individually before adopting group | Target packages, overlays resource maps, signed APK ownership, density/UI tests |
| Lineage Health permissions | Preserved, now conditional `PE_A17_PORT_LINEAGE_HEALTH_PERMISSIONS=true` | Actual HAL package owner, VINTF instance, application grants; **not** general platform inheritance |
| Qualcomm Protobuf vendorcompat | Preserved, conditional `PE_A17_PORT_QCOM_VENDORCOMPAT=true` | Prove vendor binary consumes these ABIs and modules build on AOSP17; never force QCOM into generic base |
| Legacy `ro.boot.vendor.overlay.theme` assignment | Removed from generic product properties | Android17-compatible navigation mode overlay/Settings selection |
| `persist.sys.disable_rescue=true`, ADB auth and USB override | Removed from `common.mk`; retain native AOSP17 safety policy | Explicit product/security assessment only if a real regression requires a change |
| Legacy NTFS, TextClassifier, charger and wallet targets | Still present in historical `common.mk`; **unverified** rather than assumed compatible | Module ownership/dependencies from full Soong graph; reconcile with Mainline replacements |
| OTA updater init and `ota.mk` | Historical code remains; `ota.mk` not auto-inherited | New PE updater module ownership, signed update flow, SELinux and A/B OTA |

### Important limitations

- A `PE_A17_PORT_*=true` flag only restores a **historical module selection**, not compatibility. None of these optional legacy targets is declared successfully ported by that flag. Do not enable one in a release configuration without its corresponding code/API, licensing and platform build proof.
- The original `config/rro_overlays.mk` remains intact for migration review, not an approved list of modern overlays. GMS-only configurations must not be conflated with base AOSP17.
- `config/common_full.mk`, `common_full_phone.mk` and `BoardConfig*.mk` remain to be audited separately. The old Qualcomm `BoardConfig.mk` includes a CAF path absent from current base-only profiles; this is a **future scoped integration** issue, not a reason to import a device tree now.
- This is a **base-platform port**. Do not start or alter mondrian device trees until the platform graph, product build and generic AOSP17 tests are ready.

## Verification ledger

- [Vendor Make/feature gating CI #41858573264](https://github.com/PixelExperience-Reborn/vendor_aosp/actions/runs/41858573264) — **PASS** on `4d6087c61907c317de8c3d714f8d3317f320f44c`. Tests include old feature retention and explicit package-selection flags. This is host GNU Make + Python/Bash testing, **not** an Android17 target build.
- Source and product change: `config/common.mk` commit `6e9e55b6ec2b4310facee60669c755e4915ca8fe`. The archived `seventeen` branch remains unchanged.
- Source graph: manifest's opt-in profile pins `vendor_aosp` and verified platform projects; the historical `default.xml` is not the production checkout path.

**Next base work:** establish a valid generic AOSP17 PE product definition, audit remaining common and BoardConfig/overlay module paths against a real Soong module graph, resolve missing dependencies (without importing LineageOS device product makefiles), compile the complete platform and only then stage device-specific bring-up. This audit does not mark P0 vendor as fully completed.
