# PE-Reborn AOSP17 — Launcher3QuickStep and GMS product source contract

Date: 2026-11-08. Scope: independent clean Android 17 platform; no mondrian tree, device features, or proprietary imports. This is staged in vendor_aosp Draft PR #1, not an Android17 compiled APK.

## Verified ownership and historical origin

- Original PixelExperience/manifest fourteen at 136aee696422bda841eb5c6a3c9279bbb6bbef02 inherited official Google platform/packages/apps/Launcher3. Its three active PixelExperience snippets did not fork Launcher3.
- The archived PixelExperience/packages_apps_Launcher3 only has oreo-mr1 from 2018 (637ad2e7aaf948390516edac57db715faf44e9ce). It is not a valid Android17 replacement.
- PixelExperience vendor_aosp fourteen at 5002afb5177d57e65248d1333312346b689a8802 placed NexusLauncherRelease and SystemUIGoogle in PRODUCT_DEXPREOPT_SPEED_APPS, **not** PRODUCT_PACKAGES. Its original config inherited separately hosted vendor/gms/products/gms.mk; without the corresponding private product source, actual Google APK packaging is not verified.
- Official Android17 platform/packages/apps/Launcher3 at tag android-17.0.0_r1 resolves to commit c612e6ece389f21c40f8cb9cd9a4b44239f00009, with Android.bp Git blob 46d199d1cac93405df1cdb70928b1f82c46212d2. The Android.bp defines android_app Launcher3 and android_app Launcher3QuickStep. The latter is privileged, system_ext_specific, platform_apis, overrides Home/Launcher2/Launcher3 and requires privapp_whitelist_com.android.launcher3 and launcher.quickstep.protolog.pb. It merges quickstep/AndroidManifest-launcher.xml and AndroidManifest-common.xml.
- Launcher3QuickStep source also links modern AOSP17 Java/Soong infrastructure (SystemUI shared library, ProtoLog, Jetpack Compose, window flags, and personalcontext_ace_*). Merely seeing Android.bp is not a successful target build.

## Actual staged PE-Reborn common product choice

config/common.mk now explicitly adds PRODUCT_PACKAGES += Launcher3QuickStep. It is the native open-source HOME/Recents baseline regardless of WITH_GMS flag, because WITH_GMS alone does not guarantee a licensed Pixel Launcher module. No Google app, APK, alternate launcher or hardware feature is added by this commit.

- WITH_GMS=true remains explicit and requires a real, independently licensed vendor/gms/products/gms.mk. The default no-GMS path does not source any proprietary package.
- Dexpreopt of NexusLauncherRelease/SystemUIGoogle still requires BOTH WITH_GMS=true and PE_A17_PORT_GOOGLE_PRIV_APPS=true. Dexpreopt is not package inclusion.
- Historical PixelLauncherCustomOverlay/NexusLauncherResOverlay remain under PE_A17_PORT_LEGACY_OVERLAYS and must be reviewed individually; old RRO groups are not active by default.
- A future GMS configuration providing another HOME/Recents app MUST reconcile launcher package overrides, permissions, roles, recents/gesture provider, partition placement, signing and VINTF/security as appropriate. Do not assume a Pixel Launcher APK is present or licensed.

## Evidence and validation

- tests/a17_launcher_gms_contract_test.py: seven independent GNU Make test methods for common, full and phone products, open-source Quickstep exactly once, no Google launcher in default packages, conditional GMS import/permissions, optional Google preopt and overlays.
- tools/a17_verify_launcher_source_contract.py: after targeted Google AOSP17 repo sync, requires exact official Launcher3 commit; parses Launcher3QuickStep Soong metadata and exported MAIN/HOME/DEFAULT activity from source manifests.
- .github/workflows/aosp17-launcher-gms-source-gate.yml: hermetic host tests plus SHA-pinned AOSP17 reference manifest targeted Launcher3 sync and source checks.
- Previous original PE14 gap reports: https://github.com/PixelExperience-Reborn/manifest/blob/port/a17-aosp17-manifest-20261102/docs/ANDROID_17_ORIGINAL_PE14_REPOSITORY_COVERAGE_AUDIT.md and https://github.com/PixelExperience-Reborn/manifest/blob/port/a17-aosp17-manifest-20261102/docs/ANDROID_17_ORIGINAL_PE_GITHUB_373_REPOSITORY_GAP_AUDIT.md.

## Remaining blockers

- Full repo sync and Android17 Soong bootstrap, real m Launcher3QuickStep build, image inclusion, merged manifest, privapp permissions, HOME resolution/Quickstep runtime and device boot were NOT run or demonstrated by host tests.
- PE a17_base.mk is still an isolated branding/GMS smoke fragment with deliberately no PRODUCT_PACKAGES; it is not a shipping product. The real common.mk selection is effective only once inherited by a genuine Android17 product.
- GMS licenses, exact vendor/gms APK inventory, Google app signatures, SetupWizard/WebView/privapp overlays, compatibility and release test remain separate. Do not silently reintroduce old PE14 proprietary app blobs.
- This source audit does not justify importing 238 historic GitHub repositories or any LineageOS device tree, nor radio FM extras.

Official source: https://android.googlesource.com/platform/packages/apps/Launcher3/+/refs/tags/android-17.0.0_r1/Android.bp
