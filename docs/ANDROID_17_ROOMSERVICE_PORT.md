# PixelExperience-Reborn — Android 17 roomservice audit (stage 8)

**Status: draft, read-only, not a validated device port.** This patch changes only the historical `vendor/aosp/build/tools/roomservice.py` and adds tests/documentation. It preserves the existing `vendor_aosp` PR branch and makes no changes to Android 17 AOSP repositories.

## Source findings

The historic PE `roomservice.py` used a GitHub search against `PixelExperience-Devices`, picked branches based on the older `fourteen` default, edited `.repo/local_manifests/pixel.xml` and executed `repo sync` (including recursive `aosp.dependencies`). It implicitly trusted device-provided dependency paths and repository names. That behavior is **not appropriate** for a platform-only AOSP 17 migration scoped to `mondrian`.

The accessible `LF52406/mondrian_android_device_xiaomi_mondrian` tree at `lineage-24.0` contains `AndroidProducts.mk` pointing to `lineage_mondrian.mk`; a compatible `aosp_mondrian` product for Android 17 has **not** been verified. No `aosp.dependencies` file was present at the checked branch path; absence is not proof that the device has no dependencies.

## Changes

- Device scope is explicitly limited to `mondrian`; no other codename is accepted.
- Legacy CLI `roomservice.py aosp_mondrian` and dependencies-only `roomservice.py aosp_mondrian true` remain parseable.
- `PLATFORM_BRANCH = 'seventeen'` is informational for the PE platform only. **Never assume that external device trees, blobs, modules or kernels have a `seventeen` branch.**
- Scans local manifest project paths and the presence of the checked-out device tree; errors do not mutate the filesystem.
- If the tree exists and has `aosp.dependencies`, validates paths against mondrian-specific allowlisted locations, repository ownership against the maintainer's `LF52406` forks, and requires explicit revision for every dependency. Entries are **reported only**, never cloned.
- No GitHub API search, access tokens, network reads, writes to local manifests, `os.system`, shell execution or `repo sync`. This is deliberate until device dependency mappings are explicitly reviewed and Android 17 compatibility is confirmed.

## Usage on a Linux checkout

```bash
cd "$ANDROID_BUILD_TOP"
python3 vendor/aosp/build/tools/roomservice.py aosp_mondrian
python3 vendor/aosp/build/tools/roomservice.py aosp_mondrian true --json
python3 -m unittest discover -s vendor/aosp/tests -p 'a17_roomservice_test.py' -v
```

A missing tree causes a nonzero status with instructions to provide an explicitly reviewed **local manifest**; there is no automatic source discovery. `roomservice.py` is a dependency audit, **not** a replacement for the AOSP product definitions or for `repo sync`.

## Tests and acceptance gates

14 isolated Python unit tests: allowed device; denial of foreign device or injection; missing tree; local manifest scanning; malformed XML; valid dependency list; rejection of outside paths, foreign owners, missing revisions, traversal and duplicates; no filesystem writes. No full AOSP 17 build or real device boot was performed.

Before merging into `seventeen`, verify (1) compatible `aosp_mondrian` product & release mapping, (2) matching device/common/vendor/kernel dependencies and branches, (3) `repo manifest -r`, `repo sync`, Soong bootstrap, (4) product build and first boot, and (5) PE OTA/signing/versioning independently.

## Out of scope

Do not create additional device trees in the PE organization. Do not use legacy PixelExperience-Devices search, pretend lineage device branches are already adapted, add GMS blobs, or alter fingerprint, security patches, SELinux or OTA through this patch.
