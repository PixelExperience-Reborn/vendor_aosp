# PixelExperience-Reborn — independent AOSP 17 platform-only product baseline.
#
# This is the entry point for a future native Android 17 PE product, NOT the
# archived Android 14 vendor/aosp/config/common.mk and NOT a device tree.
# Keep base bring-up independent of LineageOS product makefiles, Google APKs,
# Qualcomm platform forks, legacy settings/face unlock/camera apps and RROs.
#
# Explicitly inherit this file from the native product definition once the
# platform has passed Soong/Make and generic target validation.
#
# Copyright (C) 2026 PixelExperience-Reborn
# SPDX-License-Identifier: Apache-2.0

$(call inherit-product, vendor/aosp/config/branding.mk)

PRODUCT_BRAND ?= PixelExperience

# The platform remains in charge of system security patch, signing, SDK,
# build fingerprint, system UI, settings, updater and module/APEX selection.
# Do not disable Rescue Party or AVB to get early builds to succeed.
PRODUCT_SYSTEM_PROPERTIES += \
    ro.control_privapp_permissions=enforce

# Google components are optional and can only be built from a separately
# authorized, licensed source. Never assume proprietary Google packages exist.
ifeq ($(WITH_GMS),true)
ifeq ($(wildcard vendor/gms/products/gms.mk),)
$(error PE-Reborn AOSP17: WITH_GMS=true requires a licensed vendor/gms/products/gms.mk)
endif
$(call inherit-product, vendor/gms/products/gms.mk)
endif

# Intentionally no PRODUCT_PACKAGES, overlays, HALs, SELinux rules, OTA
# plugins, or device/SoC BoardConfig overrides here. AOSP17 already owns
# SystemUI, Settings, Camera2, NFC, OTA, AVB and the Mainline components.
# Each future PE-specific module must be reviewed, compiled and enabled
# separately rather than inherited from the historic PE common.mk.
