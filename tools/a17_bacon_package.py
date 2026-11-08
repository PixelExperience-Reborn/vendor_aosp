#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Make a byte-for-byte PixelExperience-named copy of an existing AOSP OTA.

No keys are read, no OTA is generated/signed, and no installation is done.
This is deliberately not an AVB/OTA validation or release approval tool.
"""

import argparse
import hashlib
import os
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

CHUNK = 1024 * 1024
VALID_NAME = re.compile(r"^PixelExperience_[A-Za-z0-9_.-]+\.zip$")


def sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as file:
        for chunk in iter(lambda: file.read(CHUNK), b''):
            digest.update(chunk)
    return digest.hexdigest()


def is_ota_zip(path):
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            # A/B OTA carries payload.bin + payload_properties.txt.
            # Legacy recovery packages may carry META-INF/com/google/android/update-binary.
            # Do not accept arbitrary ZIP archives as OTA packages.
            ab = 'payload.bin' in names and 'payload_properties.txt' in names
            recovery = 'META-INF/com/google/android/update-binary' in names
            return ab or recovery
    except (OSError, ValueError, zipfile.BadZipFile):
        return False


def prepare(ota: Path, output: Path):
    if not str(ota).strip() or not str(output).strip():
        raise ValueError('OTA input and PE output must be nonempty')
    if not ota.is_file() or ota.is_symlink():
        raise ValueError('Missing or symlinked AOSP OTA: ' + str(ota))
    if not output.parent.is_dir():
        raise ValueError('Output directory missing: ' + str(output.parent))
    if not VALID_NAME.fullmatch(output.name):
        raise ValueError('Invalid PE ZIP name: ' + output.name)
    if output.is_symlink():
        raise ValueError('Output ZIP is a symlink; refusing')
    if ota.resolve() == output.resolve():
        raise ValueError('Input and output refer to the same file')
    if ota.stat().st_size == 0 or not is_ota_zip(ota):
        raise ValueError('Input is not a valid A/B or recovery OTA ZIP')
    sidecar = output.with_name(output.name + '.sha256sum')
    if sidecar.is_symlink():
        raise ValueError('Checksum file is a symlink; refusing')
    return sidecar


def create(ota, output):
    ota, output = Path(ota), Path(output)
    checksum = prepare(ota, output)
    original = sha256(ota)
    if output.exists():
        if not output.is_file() or sha256(output) != original:
            raise ValueError('Different output already exists; refusing to overwrite: ' + str(output))
        # Idempotent existing ZIP: only repair/rewrite the sidecar.
        print('Existing PE ZIP matches source; preserving bytes.')
    else:
        tmp = None
        try:
            with tempfile.NamedTemporaryFile(dir=output.parent, prefix='.pe-bacon-', suffix='.zip', delete=False) as f:
                tmp = Path(f.name)
                with open(ota, 'rb') as source:
                    shutil.copyfileobj(source, f, CHUNK)
                f.flush()
                os.fsync(f.fileno())
            if sha256(tmp) != original:
                raise ValueError('Copy SHA-256 mismatch')
            # Android/Termux Python does not necessarily provide os.link().
            # Create the destination exclusively instead: O_EXCL prevents
            # overwriting an OTA created by another process in the meantime.
            # Unlike a hard-link this publishes an in-progress file; on any
            # handled copy/verification failure we remove only our own file.
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            fd = os.open(output, flags, 0o600)
            try:
                with os.fdopen(fd, 'wb') as dest:
                    fd = -1  # fdopen owns descriptor now
                    with open(tmp, 'rb') as source:
                        shutil.copyfileobj(source, dest, CHUNK)
                    dest.flush()
                    os.fsync(dest.fileno())
                if sha256(output) != original:
                    raise ValueError('Published PE ZIP SHA-256 mismatch')
            except BaseException:
                # After exclusive creation, this file belongs to us. Do not
                # leave a partial/invalid ZIP if a copy or fsync fails.
                output.unlink(missing_ok=True)
                raise
            finally:
                if fd >= 0:
                    os.close(fd)
        finally:
            if tmp is not None:
                tmp.unlink(missing_ok=True)
    # The SHA file is never evidence of cryptographic OTA authenticity.
    data = f'{original}  {output.name}\n'.encode('ascii')
    tmp_sidecar = None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent, prefix='.pe-sha256-', delete=False) as f:
            tmp_sidecar = Path(f.name)
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        if checksum.is_symlink():
            raise ValueError('Checksum file became a symlink')
        os.replace(tmp_sidecar, checksum)
    finally:
        if tmp_sidecar is not None:
            tmp_sidecar.unlink(missing_ok=True)
    print(f'PE package: {output}')
    print(f'SHA-256: {original}')
    print('Archive was copied, not signed or OTA-validated.')
    return original


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ota', required=True, help='AOSP generated OTA ZIP')
    parser.add_argument('--output', required=True, help='PixelExperience_*.zip in PRODUCT_OUT')
    args = parser.parse_args(argv)
    try:
        create(args.ota, args.output)
    except (OSError, ValueError) as exc:
        parser.exit(1, 'ERROR: ' + str(exc) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
