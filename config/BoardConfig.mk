# PixelExperience-Reborn Android 17 — board configuration integration.
#
# Historic PE board/kernel/QCOM helpers are retained as migration sources,
# but Android17 generic platform products must not silently import legacy
# kernel toolchains, a nonexistent CAF build tree or unported Soong namespaces.
# This file intentionally does not select any device-specific configuration.
#
# SPDX-License-Identifier: Apache-2.0

# Keep the historical PE kernel Make implementation available only when a
# modern device/ABI validation explicitly approves its toolchain dependencies.
ifeq ($(PE_A17_PORT_LEGACY_KERNEL_BUILD),true)
include vendor/aosp/config/BoardConfigKernel.mk
endif

# Qualcomm BoardConfig is not a generic PE platform dependency. When a
# future device requests it, require the actual source rather than hiding
# a missing dependency or cloning another ROM's board configuration.
ifeq ($(BOARD_USES_QCOM_HARDWARE),true)
ifeq ($(wildcard hardware/qcom-caf/common/BoardConfigQcom.mk),)
$(error PE-Reborn AOSP17: BOARD_USES_QCOM_HARDWARE=true requires a ported Qualcomm BoardConfig; hardware/qcom-caf/common is not in the current base profile)
endif
include hardware/qcom-caf/common/BoardConfigQcom.mk
endif

# Preserve per-device/partition AVB configuration and release key policy.
# No automatic custom key selection and no changes to rollback indexes.
ifneq ($(filter OFFICIAL CI,$(CUSTOM_BUILD_TYPE)),)
ifeq ($(TARGET_USES_CUSTOM_AVB_KEY),true)
include vendor/aosp/config/BoardConfigAvb.mk
endif
endif

# The old customGlobalVars/QcomVars maps are not an Android17 Soong ABI.
# Review each actual consumer before importing this historical namespace.
ifeq ($(PE_A17_PORT_LEGACY_SOONG_CONFIG),true)
include vendor/aosp/config/BoardConfigSoong.mk
endif

# Legacy fwk-detect is a Qualcomm-specific source namespace; never publish
# a non-existent default path in the platform-only Soong dependency graph.
ifeq ($(PE_A17_PORT_FWK_DETECT),true)
ifeq ($(strip $(TARGET_FWK_DETECT_PATH)),)
$(error PE-Reborn AOSP17: PE_A17_PORT_FWK_DETECT requires TARGET_FWK_DETECT_PATH)
endif
ifeq ($(wildcard $(TARGET_FWK_DETECT_PATH)/fwk-detect/Android.bp),)
$(error PE-Reborn AOSP17: fwk-detect/Android.bp missing at TARGET_FWK_DETECT_PATH=$(TARGET_FWK_DETECT_PATH))
endif
PRODUCT_SOONG_NAMESPACES += $(TARGET_FWK_DETECT_PATH)/fwk-detect
endif
