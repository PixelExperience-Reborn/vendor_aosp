# Compatibility stub for older PE build/core/main.mk inclusion sites.
# On Android 17, vendor/aosp/config/common.mk inherits config/branding.mk,
# which exports the PE-only product properties to PRODUCT_SYSTEM_PROPERTIES.
#
# Do not set BUILD_FINGERPRINT, BUILD_VERSION_TAGS, BUILD_KEYS, BUILD_ID,
# BUILD_NUMBER, DEFAULT_SYSTEM_DEV_CERTIFICATE or security-patch overrides here.
# The matching AOSP 17 build/make, build/release and signing tools own those.
# Keeping this file as a no-op prevents duplicate properties in mixed ports.
