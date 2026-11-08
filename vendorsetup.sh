# PixelExperience-Reborn: AOSP 17 compatibility.
# Products and release configs are discovered from each device's
# AndroidProducts.mk and build/release configurations by AOSP list_products,
# list_releases and lunch. `lunch_others_targets` was a pre-release AOSP API.
# Do not fetch the old PixelExperience/official_devices JSON here: it only
# contained Android 14 device entries, and Reborn intentionally has no device
# trees for other phones. This vendorsetup is deliberately side-effect-free.

# AOSP 17's build/envsetup.sh calls source_vendorsetup(), which sources
# vendor/aosp/vendorsetup.sh. Load PE's optional helper functions here
# instead of patching the core AOSP build/make envsetup.sh.
# Do not override AOSP lunch or discover/download any device trees.
if ! type gettop >/dev/null 2>&1; then
    echo "PixelExperience: source the AOSP build/envsetup.sh first." >&2
    return 1
fi

_pe_vendor_top="$(gettop)"
if [[ -z "${_pe_vendor_top}" ]]; then
    echo "PixelExperience: unable to locate the Android source root." >&2
    unset _pe_vendor_top
    return 1
fi

_pe_vendor_helpers="${_pe_vendor_top}/vendor/aosp/build/envsetup.sh"
if [[ ! -r "${_pe_vendor_helpers}" ]]; then
    echo "PixelExperience: missing vendor/aosp/build/envsetup.sh." >&2
    unset _pe_vendor_top _pe_vendor_helpers
    return 1
fi

# shellcheck disable=SC1090
. "${_pe_vendor_helpers}"
_pe_vendor_status=$?
unset _pe_vendor_top _pe_vendor_helpers
return "${_pe_vendor_status}"
