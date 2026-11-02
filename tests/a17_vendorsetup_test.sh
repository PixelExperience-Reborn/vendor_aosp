#!/usr/bin/env bash
# Regression guard: sourcing vendorsetup must not query legacy official_devices
# or populate deprecated lunch_others_targets in an AOSP 17 environment.
set -euo pipefail
[[ $# -eq 1 ]] || { echo 'Usage: test <vendorsetup.sh>' >&2; exit 2; }
unset lunch_others_targets
# shellcheck disable=SC1090
source "$1"
[[ ! ${lunch_others_targets+x} ]] || { echo 'FAIL: legacy lunch choices populated' >&2; exit 1; }
echo 'PASS: AOSP 17 vendorsetup has no legacy device discovery side effects'
