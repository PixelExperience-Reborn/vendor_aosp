# Branding
$(call inherit-product, vendor/aosp/config/branding.mk)

PRODUCT_BRAND ?= PixelExperience

# GMS client-ID properties apply only when GMS is actually selected.
ifeq ($(WITH_GMS),true)
ifeq ($(PRODUCT_GMS_CLIENTID_BASE),)
PRODUCT_SYSTEM_DEFAULT_PROPERTIES += \
    ro.com.google.clientidbase=android-google

PRODUCT_PRODUCT_PROPERTIES += \
    ro.com.google.clientidbase=android-google

else
PRODUCT_SYSTEM_DEFAULT_PROPERTIES += \
    ro.com.google.clientidbase=$(PRODUCT_GMS_CLIENTID_BASE)

PRODUCT_PRODUCT_PROPERTIES += \
    ro.com.google.clientidbase=$(PRODUCT_GMS_CLIENTID_BASE)

endif
endif

PRODUCT_SYSTEM_DEFAULT_PROPERTIES += \
    dalvik.vm.debug.alloc=0 \
    ro.com.android.dataroaming=false \
    ro.com.android.dateformat=MM-dd-yyyy

ifeq ($(WITH_GMS),true)
PRODUCT_SYSTEM_DEFAULT_PROPERTIES += \
    ro.url.legal=http://www.google.com/intl/%s/mobile/android/basic/phone-legal.html \
    ro.url.legal.android_privacy=http://www.google.com/intl/%s/mobile/android/basic/privacy.html \
    ro.error.receiver.system.apps=com.google.android.gms \
    ro.atrace.core.services=com.google.android.gms,com.google.android.gms.ui,com.google.android.gms.persistent
endif

# Android 17 owns ADB authorization and USB defaults by build variant.
# Do not override ro.adb.secure or persist.sys.usb.config from the PE product.
# Preserve AOSP17 Rescue Party and StrictMode behavior.

# Keep historical Lineage Health support for later HAL/permission review.
# It is NOT a core dependency of the independent PE-Reborn platform.
ifeq ($(PE_A17_PORT_LINEAGE_HEALTH_PERMISSIONS),true)
PRODUCT_COPY_FILES += \
    vendor/aosp/config/permissions/privapp-permissions-lineagehw.xml:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/permissions/privapp-permissions-lineagehw.xml \
    vendor/aosp/config/permissions/org.lineageos.health.xml:$(TARGET_COPY_OUT_PRODUCT)/etc/permissions/org.lineageos.health.xml
endif

# Copy all custom init rc files
PRODUCT_COPY_FILES += \
    vendor/aosp/prebuilt/common/etc/init/init.pixelexperience-updater.rc:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/init/init.pixelexperience-updater.rc

# Enable SIP+VoIP on all targets
PRODUCT_COPY_FILES += \
    frameworks/native/data/etc/android.software.sip.voip.xml:system/etc/permissions/android.software.sip.voip.xml

# Enable wireless Xbox 360 controller support
PRODUCT_COPY_FILES += \
    frameworks/base/data/keyboards/Vendor_045e_Product_028e.kl:$(TARGET_COPY_OUT_PRODUCT)/usr/keylayout/Vendor_045e_Product_0719.kl

# Enforce privapp-permissions whitelist
PRODUCT_SYSTEM_DEFAULT_PROPERTIES += \
    ro.control_privapp_permissions=enforce

# Power whitelist
PRODUCT_COPY_FILES += \
    vendor/aosp/config/permissions/custom-power-whitelist.xml:system/etc/sysconfig/custom-power-whitelist.xml

# Do not include art debug targets
PRODUCT_ART_TARGET_INCLUDE_DEBUG_BUILD := false

# Strip the local variable table and the local variable type table to reduce
# the size of the system image. This has no bearing on stack traces, but will
# leave less information available via JDWP.
PRODUCT_MINIMIZE_JAVA_DEBUG_INFO := true

# Charger
PRODUCT_PACKAGES += \
    charger_res_images \
    product_charger_res_images \
    product_charger_res_images_vendor

# Filesystems tools
PRODUCT_PACKAGES += \
    fsck.ntfs \
    mke2fs \
    mkfs.ntfs \
    mount.ntfs

# Storage manager
PRODUCT_SYSTEM_DEFAULT_PROPERTIES += \
    ro.storage_manager.enabled=true

# Media
PRODUCT_SYSTEM_DEFAULT_PROPERTIES += \
    media.recorder.show_manufacturer_and_model=true

# Static PE overlays must be reviewed for Android17 resource contracts.
ifeq ($(PE_A17_PORT_LEGACY_OVERLAYS),true)
PRODUCT_ENFORCE_RRO_EXCLUDED_OVERLAYS += \
    vendor/aosp/overlay

PRODUCT_PACKAGE_OVERLAYS += \
    vendor/aosp/overlay/common
endif

# Legacy TouchGestures requires a reviewed Android17 framework/service port.
# Retain the historical package selection only as an explicit port candidate.
ifeq ($(PE_A17_PORT_TOUCH_GESTURES),true)
PRODUCT_PACKAGES += \
    TouchGestures
endif

# One Handed mode
PRODUCT_PRODUCT_PROPERTIES += \
    ro.support_one_handed_mode?=true \

# GMS alone does not supply audited SystemUIGoogle/NexusLauncherRelease
# modules. Never request preopt of absent or unreviewed privileged Google apps.
ifeq ($(WITH_GMS),true)
ifeq ($(PE_A17_PORT_GOOGLE_PRIV_APPS),true)
PRODUCT_DEXPREOPT_SPEED_APPS += \
    SystemUIGoogle \
    NexusLauncherRelease
endif
endif

PRODUCT_SYSTEM_DEFAULT_PROPERTIES += \
    dalvik.vm.systemuicompilerfilter=speed

# SystemUI plugins
PRODUCT_PACKAGES += \
    QuickAccessWallet

# Google keyboard and SetupWizard settings only when GMS is enabled.
ifeq ($(WITH_GMS),true)
# Gboard configuration
PRODUCT_PRODUCT_PROPERTIES += \
    ro.com.google.ime.theme_id=5 \
    ro.com.google.ime.system_lm_dir=/product/usr/share/ime/google/d3_lms

# SetupWizard configuration
PRODUCT_PRODUCT_PROPERTIES += \
    ro.setupwizard.enterprise_mode=1 \
    ro.setupwizard.rotation_locked=true \
    setupwizard.enable_assist_gesture_training=true \
    setupwizard.theme=glif_v3_light \
    setupwizard.feature.baseline_setupwizard_enabled=true \
    setupwizard.feature.skip_button_use_mobile_data.carrier1839=true \
    setupwizard.feature.show_pai_screen_in_main_flow.carrier1839=false \
    setupwizard.feature.show_pixel_tos=false
endif

# StorageManager configuration
PRODUCT_PRODUCT_PROPERTIES += \
    ro.storage_manager.show_opt_in=false

# Google-specific product metadata only when GMS is enabled.
ifeq ($(WITH_GMS),true)
# OPA configuration
PRODUCT_PRODUCT_PROPERTIES += \
    ro.opa.eligible_device=true

# Google legal
PRODUCT_PRODUCT_PROPERTIES += \
    ro.url.legal=http://www.google.com/intl/%s/mobile/android/basic/phone-legal.html \
    ro.url.legal.android_privacy=http://www.google.com/intl/%s/mobile/android/basic/privacy.html

# Google Play services configuration
PRODUCT_PRODUCT_PROPERTIES += \
    ro.error.receiver.system.apps=com.google.android.gms \
    ro.atrace.core.services=com.google.android.gms,com.google.android.gms.ui,com.google.android.gms.persistent
endif

# TextClassifier
PRODUCT_PACKAGES += \
	libtextclassifier_annotator_en_model \
	libtextclassifier_annotator_universal_model \
	libtextclassifier_actions_suggestions_universal_model \
	libtextclassifier_lang_id_model

# Keep legacy Qualcomm vendorcompat libraries device-scoped. The base
# cannot assume Android14 vendor blob ABI or old protobuf modules.
ifeq ($(PE_A17_PORT_QCOM_VENDORCOMPAT),true)
PRODUCT_PACKAGES += \
    libprotobuf-cpp-full-3.9.1-vendorcompat \
    libprotobuf-cpp-lite-3.9.1-vendorcompat
endif

# Camera2 remains the official Android17 default. Port Aperture as an
# optional PE feature only after its CameraX/Soong and runtime validation.
ifeq ($(PE_A17_PORT_APERTURE),true)
ifneq ($(PRODUCT_NO_CAMERA),true)
PRODUCT_PACKAGES += \
    Aperture
endif
endif

# AOSP17 navigation mode is selected through compatible resource overlays
# and Settings, not by spoofing ro.boot.vendor.overlay.theme.

# Pixel customization
TARGET_SUPPORTS_GOOGLE_RECORDER ?= true
TARGET_INCLUDE_STOCK_ARCORE ?= true
TARGET_INCLUDE_LIVE_WALLPAPERS ?= true
TARGET_SUPPORTS_QUICK_TAP ?= false
TARGET_SUPPORTS_CALL_RECORDING ?= true

# The old FaceUnlockService is privileged and unported on AOSP17. Never
# advertise face hardware or package the service from a generic product
# without a separately reviewed implementation and a real HAL.
TARGET_FACE_UNLOCK_SUPPORTED ?= false
ifeq ($(PE_A17_PORT_FACE_UNLOCK),true)
ifeq ($(TARGET_FACE_UNLOCK_SUPPORTED),true)
PRODUCT_PACKAGES += \
    FaceUnlockService
PRODUCT_SYSTEM_DEFAULT_PROPERTIES += \
    ro.face_unlock_service.enabled=$(TARGET_FACE_UNLOCK_SUPPORTED)
PRODUCT_COPY_FILES += \
    frameworks/native/data/etc/android.hardware.biometrics.face.xml:$(TARGET_COPY_OUT_SYSTEM)/etc/permissions/android.hardware.biometrics.face.xml
endif
endif

# Keep the former Google launcher overlay as an optional PE migration item.
ifeq ($(PE_A17_PORT_LEGACY_OVERLAYS),true)
PRODUCT_PACKAGES += \
    NexusLauncherResOverlay
endif

# Audio
$(call inherit-product, vendor/aosp/config/audio.mk)

# Bootanimation
$(call inherit-product, vendor/aosp/config/bootanimation.mk)

# Fonts
$(call inherit-product, vendor/aosp/config/fonts.mk)

# Proprietary GMS is deliberately opt-in. An AOSP-only bring-up must not
# depend on unlicensed or unavailable Google packages.
# For an explicitly GMS-enabled build, fail early if the licensed source is
# absent rather than silently producing a misleading PE/GMS image.
# Existing product configurations can enable this with WITH_GMS=true.
# GMS
ifeq ($(WITH_GMS),true)
ifeq ($(wildcard vendor/gms/products/gms.mk),)
$(error PixelExperience: WITH_GMS=true requires a licensed vendor/gms/products/gms.mk)
endif
$(call inherit-product, vendor/gms/products/gms.mk)
endif

# OTA
#$(call inherit-product, vendor/aosp/config/ota.mk)

# The old Pixel RRO group targets old system/Google packages. Preserve its
# inventory, but require an explicit target-by-target AOSP17 port decision.
ifeq ($(PE_A17_PORT_LEGACY_OVERLAYS),true)
$(call inherit-product, vendor/aosp/config/rro_overlays.mk)
endif

# The historical vendor/pixel-framework config.mk overrides AOSP SystemUI
# and Settings with platform-signed APKs. Do not auto-include it in AOSP17.
# Its source/ABI/license/security review is tracked separately.

-include $(WORKSPACE)/build_env/image-auto-bits.mk
