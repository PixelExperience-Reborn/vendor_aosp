#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Read-only preflight for PE Android 17 target-files and optional OTA ZIP.

This is NOT a cryptographic signature verification, firmware safety approval,
AVB trust-chain verification, or permission to distribute/install the build.
"""
import argparse
import json
import re
import sys
import zipfile
from pathlib import Path


def _parse_info(contents):
    values = {}
    for line in contents.splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            k, v = line.split('=', 1)
            values[k.strip()] = v.strip()
    return values


def _public_test_key(key):
    norm = key.replace('\\', '/').lower()
    return ('external/avb/test/' in norm or
            'build/make/target/product/security/' in norm or
            norm.endswith('/testkey') or norm.endswith('/testkey.pk8') or
            'testkey_rsa' in norm)


def inspect(target_zip, ota_zip=None):
    errors, warnings = [], []
    with zipfile.ZipFile(target_zip, 'r') as z:
        names = set(z.namelist())
        if 'META/misc_info.txt' not in names:
            return {'errors': ['target-files missing META/misc_info.txt'],
                    'warnings': [], 'metadata': {}}
        info = _parse_info(z.read('META/misc_info.txt').decode('utf-8', 'replace'))
        if info.get('avb_enable') != 'true':
            errors.append('AVB is not enabled in target-files metadata')
        key_fields = {k: v for k, v in info.items()
                      if (k.startswith('avb_') and 'key_path' in k)
                      or k == 'default_system_dev_certificate'}
        for key, value in key_fields.items():
            if _public_test_key(value):
                errors.append(f'{key} refers to a public test key')
        if not key_fields:
            warnings.append('No signing-key paths in misc_info; inspect signing configuration separately')
        for key, value in info.items():
            if key.startswith('avb_') and ('args' in key or 'flags' in key):
                if re.search(r'(?<!\S)--flags(?:\s+|=)(?:1|2|3)(?!\d)', value):
                    errors.append(f'{key} contains disabled verification flags')
        if info.get('ab_update') == 'true':
            if 'META/ab_partitions.txt' not in names:
                errors.append('A/B target-files missing META/ab_partitions.txt')
        else:
            warnings.append('Target-files does not declare ab_update=true; confirm device OTA format')
        if 'META/otakeys.txt' not in names:
            warnings.append('META/otakeys.txt absent; inspect OTA public-key configuration')
    if ota_zip is not None:
        with zipfile.ZipFile(ota_zip, 'r') as z:
            names = set(z.namelist())
            if info.get('ab_update') == 'true':
                for required in ('payload.bin', 'payload_properties.txt'):
                    if required not in names:
                        errors.append(f'A/B OTA ZIP missing {required}')
                if ('META-INF/com/android/metadata' not in names and
                        'META-INF/com/android/metadata.pb' not in names):
                    warnings.append('OTA metadata entry not found at typical A/B paths')
            elif 'META-INF/com/android/metadata' not in names:
                warnings.append('OTA legacy metadata not found')
    return {'errors': errors, 'warnings': warnings,
            'metadata': {'avb_enable': info.get('avb_enable', '<unset>'),
                         'ab_update': info.get('ab_update', '<unset>'),
                         'key_fields_present': sorted(key_fields),
                         'target_files': str(Path(target_zip).name),
                         'ota': str(Path(ota_zip).name) if ota_zip else None}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target-files', required=True, type=Path)
    parser.add_argument('--ota', type=Path)
    args = parser.parse_args()
    for path in (args.target_files, args.ota):
        if path is not None and not path.is_file():
            parser.error(f'File not found: {path}')
    try:
        report = inspect(args.target_files, args.ota)
    except (OSError, zipfile.BadZipFile) as exc:
        parser.error(f'Invalid release archive: {exc}')
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print('NOTE: metadata inspection is NOT AVB or OTA signature verification.', file=sys.stderr)
    return 1 if report['errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
