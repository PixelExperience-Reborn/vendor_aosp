# Telephony

IS_PHONE := true

# World APN list
PRODUCT_PACKAGES += \
    apns-conf.xml

# Telephony packages
PRODUCT_PACKAGES += \
    Stk

# Android17's Tethering module owns carrier entitlement/provisioning.
# Retain the original PE property only as an explicit, independently reviewed
# product exception; never bypass entitlement for all phone builds.
ifeq ($(PE_A17_PORT_LEGACY_TETHERING_BYPASS),true)
PRODUCT_SYSTEM_PROPERTIES += \
    net.tethering.noprovisioning=true
endif

# Inherit full common PixelExperience stuff
$(call inherit-product, vendor/aosp/config/common_full.mk)
