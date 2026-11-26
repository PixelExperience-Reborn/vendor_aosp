# Release configuration contributions

AOSP 17 sets the platform security patch level (`ro.build.version.security_patch`)
from the release flag `RELEASE_PLATFORM_SECURITY_PATCH` of the release
configuration (`TARGET_RELEASE`). `android-17.0.0_r1` (`cp2a`) sets `2026-06-05`.

Google publishes the monthly Android 17 security fixes as
`android-security-17.0.0_rN` tags, which branch off before `r1`. The
PixelExperience-Reborn tree brings every fix of the newest tag into each
project it touches (manifest `aosp17_pe_mondrian_build.xml`): forks with AOSP
history merge the tag, snapshot forks carry the fixes as `cherry-pick -x`
commits, and projects whose tag contents include all of `r1` follow the tag.
Each result was checked to equal the true merge of `r1` and the tag.

| Tag | Bulletin | Patch level set here |
| --- | --- | --- |
| `android-security-17.0.0_r3` (tagged 2026-11-02) | up to September 2026 | `2026-09-01` |

The level is `-01`: it covers the Android platform fixes. The `-05` level also
requires the kernel and closed-source vendor fixes of the month, which the
stock OS3.0.8.0 vendor and kernel components do not all carry; the vendor
patch level is that of the stock vendor (`VENDOR_SECURITY_PATCH` in the
device tree).

Each new tag: bring its fixes into the same projects, then update the flag
value and this table.
