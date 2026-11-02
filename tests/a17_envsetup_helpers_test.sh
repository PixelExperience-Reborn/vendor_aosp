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

assert_lunch() {
    local expected="$1"
    [[ "${LUNCH_CALLS[-1]}" == "$expected" ]] || {
        printf 'FAILED: expected lunch <%s>, got <%s>\n' "$expected" "${LUNCH_CALLS[-1]}" >&2
        exit 1
    }
}

breakfast mondrian
assert_lunch 'aosp_mondrian|trunk_staging|userdebug'

breakfast mondrian user
assert_lunch 'aosp_mondrian|trunk_staging|user'

breakfast mondrian eng a17_release
assert_lunch 'aosp_mondrian|a17_release|eng'

breakfast aosp_mondrian-userdebug
assert_lunch 'aosp_mondrian|trunk_staging|userdebug'

breakfast aosp_mondrian-trunk_staging-user
assert_lunch 'aosp_mondrian|trunk_staging|user'

PE_LUNCH_RELEASE=beta breakfast mondrian
assert_lunch 'aosp_mondrian|beta|userdebug'

if breakfast >/dev/null 2>&1; then echo 'FAIL: accepted no args' >&2; exit 1; fi
if breakfast 'mondrian;rm' >/dev/null 2>&1; then echo 'FAIL: accepted invalid product' >&2; exit 1; fi
if breakfast mondrian badvariant >/dev/null 2>&1; then echo 'FAIL: accepted invalid variant' >&2; exit 1; fi
if breakfast mondrian user bad-release >/dev/null 2>&1; then echo 'FAIL: accepted invalid release' >&2; exit 1; fi
if breakfast mondrian userdebug foo extra >/dev/null 2>&1; then echo 'FAIL: accepted excess args' >&2; exit 1; fi

brunch mondrian
assert_lunch 'aosp_mondrian|trunk_staging|userdebug'
[[ "${MKA_CALLS[-1]}" == bacon ]] || { echo 'FAIL: brunch target' >&2; exit 1; }

local_before="${#MKA_CALLS[@]}"
LUNCH_FAIL=1
if brunch mondrian >/dev/null 2>&1; then echo 'FAIL: brunch built after lunch failure' >&2; exit 1; fi
[[ "${#MKA_CALLS[@]}" -eq "$local_before" ]] || { echo 'FAIL: mka executed after lunch failure' >&2; exit 1; }

[[ "$(type -t lunch)" == function ]] || { echo 'FAIL: lunch function missing' >&2; exit 1; }
echo 'PASS: 12 PE breakfast/brunch assertions (no Android build executed)'
