# PixelExperience-Reborn AOSP 17 — optional product-configuration smoke test.
#
# This is NOT the future complete PE-Reborn product definition or a substitute
# for the historical PixelExperience common.mk feature inventory.
# It exercises only PE branding, privileged-permission enforcement and licensed
# GMS opt-in in a hermetic GNU Make fixture. No manifest profile or product
# currently inherits this fragment. The full PE product remains to be ported
# feature-by-feature and compiled against Android 17.
#
# Keep smoke tests independent of device trees and unavailable vendor modules.
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
