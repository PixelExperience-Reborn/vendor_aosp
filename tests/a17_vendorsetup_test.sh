#!/usr/bin/env bash
# Regression: AOSP17 source_vendorsetup must load PE helpers through the
# public vendor/aosp/vendorsetup.sh hook without mutating AOSP lunch or
# triggering historical automatic device discovery.
set -euo pipefail

[[ $# -eq 1 ]] || { echo "Usage: $0 <vendor/aosp/vendorsetup.sh>" >&2; exit 2; }
vendorsetup="$1"
helper="$(dirname "$vendorsetup")/build/envsetup.sh"

[[ -r "$vendorsetup" && -r "$helper" ]] || {
    echo "FAIL: vendor setup or PE helper file is missing" >&2
    exit 1
}

scratch="$(mktemp -d)"
trap 'rm -rf "$scratch"' EXIT
mkdir -p "$scratch/vendor/aosp/build"
cp "$helper" "$scratch/vendor/aosp/build/envsetup.sh"

# AOSP provides these functions before source_vendorsetup() runs.
gettop() { printf '%s\n' "$scratch"; }
lunch() { printf 'AOSP lunch: %s\n' "$*"; }
before_lunch="$(declare -f lunch)"
unset lunch_others_targets || true

# shellcheck disable=SC1090
source "$vendorsetup"

[[ "$(type -t breakfast)" == function ]] || {
    echo "FAIL: PE breakfast helper missing" >&2
    exit 1
}
[[ "$(type -t brunch)" == function ]] || {
    echo "FAIL: PE brunch helper missing" >&2
    exit 1
}
[[ "$(declare -f lunch)" == "$before_lunch" ]] || {
    echo "FAIL: PE helpers replaced AOSP lunch" >&2
    exit 1
}
[[ ! ${lunch_others_targets+x} ]] || {
    echo "FAIL: legacy lunch choices populated" >&2
    exit 1
}
breakfast --help >/dev/null
brunch --help >/dev/null

# Sourcing again must be harmless and must preserve the platform commands.
source "$vendorsetup"
[[ "$(declare -f lunch)" == "$before_lunch" ]] || {
    echo "FAIL: re-sourcing changed AOSP lunch" >&2
    exit 1
}

# Missing helper or invalid source root must fail instead of pretending
# that Android's build environment is fully configured.
if ( gettop() { printf '%s\n' "$scratch/missing"; }; source "$vendorsetup" >/dev/null 2>&1 ); then
    echo "FAIL: missing PE helper was ignored" >&2
    exit 1
fi

echo "PASS: PE helpers load through AOSP17 vendorsetup; lunch and device discovery untouched"
