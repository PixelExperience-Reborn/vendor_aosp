# PixelExperience-Reborn: AOSP 17 compatibility.
# Products and release configs are discovered from each device's
# AndroidProducts.mk and build/release configurations by AOSP list_products,
# list_releases and lunch. `lunch_others_targets` was a pre-release AOSP API.
# Do not fetch the old PixelExperience/official_devices JSON here: it only
# contained Android 14 device entries, and Reborn intentionally has no device
# trees for other phones. This vendorsetup is deliberately side-effect-free.
