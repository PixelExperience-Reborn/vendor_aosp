# PixelExperience naming metadata. Android platform version and patch level
# are controlled separately by the pinned AOSP 17 platform/build/release sources.
CUSTOM_BUILD_TYPE ?= BETA

# One UTC epoch feeds both labels, optionally fixed by the build environment.
# An official/reproducible release should provide SOURCE_DATE_EPOCH explicitly.
CUSTOM_BUILD_DATE_UTC := $(if $(strip $(SOURCE_DATE_EPOCH)),$(strip $(SOURCE_DATE_EPOCH)),$(shell date -u +%s))
CUSTOM_BUILD_DATE := $(shell date -u -d "@$(CUSTOM_BUILD_DATE_UTC)" +%Y%m%d-%H%M)

# ROM labeling only; never override AOSP PLATFORM_VERSION or SDK values.
CUSTOM_PLATFORM_VERSION := 17.0
CUSTOM_VERSION_PROP := seventeen
CUSTOM_VERSION := PixelExperience_$(CUSTOM_BUILD)-$(CUSTOM_PLATFORM_VERSION)-$(CUSTOM_BUILD_DATE)-$(CUSTOM_BUILD_TYPE)

# Product inheritance is the supported place for PE-specific system properties.
# No fingerprint, signing-tag or ro.build.version.security_patch overrides.
PRODUCT_SYSTEM_PROPERTIES += \
    org.pixelexperience.version=$(CUSTOM_VERSION_PROP) \
    org.pixelexperience.version.display=$(CUSTOM_VERSION) \
    org.pixelexperience.build_date=$(CUSTOM_BUILD_DATE) \
    org.pixelexperience.build_date_utc=$(CUSTOM_BUILD_DATE_UTC) \
    org.pixelexperience.build_type=$(CUSTOM_BUILD_TYPE)

# AOSP supplies its platform security patch from release config. Never publish
# a fabricated (or device/vendor) patch date. Only mirror a known platform value.
ifneq ($(strip $(PLATFORM_SECURITY_PATCH)),)
PRODUCT_SYSTEM_PROPERTIES += org.pixelexperience.build_security_patch=$(PLATFORM_SECURITY_PATCH)
endif
