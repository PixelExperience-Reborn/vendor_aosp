#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Print the PixelExperience-Reborn banner with build information.

Used when a build starts (after the product is selected) and when the
release package is ready. Each --info KEY=VALUE becomes one aligned line;
colors are used on a terminal only.

    pe_banner.py --title "Build started" --info "Device=mondrian" ...
"""
import argparse
import os
import sys

LOGO = r"""
  ____  _          _ _____                      _
 |  _ \(_)_  _____| | ____|_  ___ __   ___ _ __(_) ___ _ __   ___ ___
 | |_) | \ \/ / _ \ |  _| \ \/ / '_ \ / _ \ '__| |/ _ \ '_ \ / __/ _ \
 |  __/| |>  <  __/ | |___ >  <| |_) |  __/ |  | |  __/ | | | (_|  __/
 |_|   |_/_/\_\___|_|_____/_/\_\ .__/ \___|_|  |_|\___|_| |_|\___\___|
                               |_|                       R E B O R N
"""

BLUE, BOLD, GREEN, RED, RESET = "\033[1;34m", "\033[1m", "\033[1;32m", "\033[1;31m", "\033[0m"


def render(title, info, status=None, color=False):
    paint = (lambda code, text: f"{code}{text}{RESET}") if color else (lambda code, text: text)
    lines = [paint(BLUE, LOGO.rstrip("\n"))]
    width = max([len(title)] + [len(k) + len(v) + 3 for k, v in info]) + 4
    rule = "=" * max(width, 60)
    lines += ["", rule]
    head = paint(BOLD, title)
    if status is not None:
        head += "  " + (paint(GREEN, "[SUCCESS]") if status == 0 else paint(RED, f"[FAILED: {status}]"))
    lines.append("  " + head)
    lines.append(rule)
    key_width = max((len(k) for k, _ in info), default=0)
    for key, value in info:
        lines.append(f"  {paint(BOLD, key.ljust(key_width))} : {value}")
    lines += [rule, ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--title", required=True)
    parser.add_argument("--info", action="append", default=[], metavar="KEY=VALUE")
    parser.add_argument("--status", type=int, help="exit status of the build, shown as SUCCESS/FAILED")
    args = parser.parse_args()
    info = []
    for item in args.info:
        key, sep, value = item.partition("=")
        if not sep:
            parser.error(f"--info needs KEY=VALUE: {item!r}")
        if value:
            info.append((key, value))
    color = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
    print(render(args.title, info, args.status, color))
    return 0


if __name__ == "__main__":
    sys.exit(main())
