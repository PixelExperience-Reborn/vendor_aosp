#!/usr/bin/env bash
# Validate PE breakfast/brunch argument handling without running a real AOSP build.
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <vendor/aosp/build/envsetup.sh>" >&2
    exit 2
fi

# This file intentionally defines shell functions and aliases only.
# shellcheck disable=SC1090
source "$1"

LUNCH_CALLS=()
MKA_CALLS=()
LUNCH_FAIL=0
lunch() {
    LUNCH_CALLS+=("$1|$2|$3")
    [[ "$LUNCH_FAIL" -eq 0 ]]
}
mka() {
    MKA_CALLS+=("$*")
}
# Build variables of a configured product.
get_build_var() {
    case "$1" in
        TARGET_DEVICE) echo mondrian ;;
        CUSTOM_VERSION) echo PixelExperience_mondrian-17.0-20261126-1200-BETA ;;
        PLATFORM_VERSION) echo 17 ;;
        TARGET_RELEASE) echo cp2a ;;
        PRODUCT_OUT) echo /nonexistent ;;
        *) echo "" ;;
    esac
}

assert_lunch() {
    local expected="$1"
    [[ "${LUNCH_CALLS[-1]}" == "$expected" ]] || {
        printf 'FAILED: expected lunch <%s>, got <%s>\n' "$expected" "${LUNCH_CALLS[-1]}" >&2
        exit 1
    }
}

banner_file="$(mktemp)"
trap 'rm -f "$banner_file"' EXIT
breakfast mondrian > "$banner_file"
banner="$(cat "$banner_file")"
assert_lunch 'aosp_mondrian|cp2a|userdebug'
[[ "$CUSTOM_BUILD" == mondrian ]] || { echo "FAIL: CUSTOM_BUILD is <$CUSTOM_BUILD>" >&2; exit 1; }
[[ "$banner" == *'17 (cp2a)'* ]] || { echo 'FAIL: banner without the release' >&2; exit 1; }
[[ "$banner" == *'R E B O R N'* && "$banner" == *'PixelExperience_mondrian-17.0-20261126-1200-BETA'* ]] || {
    echo 'FAIL: breakfast did not print the PE banner with the build version' >&2
    exit 1
}

breakfast mondrian user >/dev/null
assert_lunch 'aosp_mondrian|cp2a|user'

breakfast mondrian eng a17_release >/dev/null
assert_lunch 'aosp_mondrian|a17_release|eng'

breakfast aosp_mondrian-userdebug >/dev/null
assert_lunch 'aosp_mondrian|cp2a|userdebug'

breakfast aosp_mondrian-trunk_staging-user >/dev/null
assert_lunch 'aosp_mondrian|trunk_staging|user'

PE_LUNCH_RELEASE=beta breakfast mondrian >/dev/null
assert_lunch 'aosp_mondrian|beta|userdebug'

# AOSP 17 removed the zero-argument lunch menu. In a non-interactive
# environment breakfast prints available products and never builds.
list_products() { printf '%s\n' aosp_mondrian aosp_cf_x86_64_phone; }
list_releases() { printf '%s\n' trunk_staging; }
noarg_text="$(breakfast </dev/null 2>&1)" && {
    echo 'FAIL: zero-argument breakfast succeeded without a terminal' >&2
    exit 1
}
[[ "$noarg_text" == *aosp_mondrian* ]] || {
    echo 'FAIL: did not show available products' >&2
    exit 1
}
if brunch --help >/dev/null 2>&1; then :; else
    echo 'FAIL: brunch --help failed' >&2
    exit 1
fi
[[ "${#MKA_CALLS[@]}" -eq 0 ]] || {
    echo 'FAIL: brunch --help unexpectedly built' >&2
    exit 1
}
if breakfast --help >/dev/null 2>&1; then :; else
    echo 'FAIL: breakfast --help failed' >&2
    exit 1
fi
if breakfast 'mondrian;rm' >/dev/null 2>&1; then echo 'FAIL: accepted invalid product' >&2; exit 1; fi
if breakfast mondrian badvariant >/dev/null 2>&1; then echo 'FAIL: accepted invalid variant' >&2; exit 1; fi
if breakfast mondrian user bad-release >/dev/null 2>&1; then echo 'FAIL: accepted invalid release' >&2; exit 1; fi
if breakfast mondrian userdebug foo extra >/dev/null 2>&1; then echo 'FAIL: accepted excess args' >&2; exit 1; fi

brunch mondrian > "$banner_file"
assert_lunch 'aosp_mondrian|cp2a|userdebug'
[[ "${MKA_CALLS[-1]}" == bacon ]] || { echo 'FAIL: brunch target' >&2; exit 1; }
grep -q 'PixelExperience build finished' "$banner_file" && grep -q 'Time' "$banner_file" || {
    echo 'FAIL: brunch did not print the finish banner with the build time' >&2
    exit 1
}

local_before="${#MKA_CALLS[@]}"
LUNCH_FAIL=1
if brunch mondrian >/dev/null 2>&1; then echo 'FAIL: brunch built after lunch failure' >&2; exit 1; fi
[[ "${#MKA_CALLS[@]}" -eq "$local_before" ]] || { echo 'FAIL: mka executed after lunch failure' >&2; exit 1; }

[[ "$(type -t lunch)" == function ]] || { echo 'FAIL: lunch function missing' >&2; exit 1; }
echo 'PASS: 12 PE breakfast/brunch assertions (no Android build executed)'
