#!/usr/bin/env python3
"""Download and verify a pre/post binary pair described by a workshop manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    binaries = manifest.get("binaries", [])
    if len(binaries) != 2:
        parser.error("manifest must describe exactly two binaries")

    args.output.mkdir(parents=True, exist_ok=True)
    for binary in binaries:
        filename = str(binary["filename"])
        expected = str(binary["sha256"]).lower()
        destination = args.output / filename
        temporary = destination.with_suffix(destination.suffix + ".part")

        if destination.is_file() and sha256(destination) == expected:
            print(f"  [ok]   {binary['role']}: {filename} {expected}")
            continue

        request = Request(str(binary["url"]), headers={"User-Agent": "RITSEC-Patch-Pair/1.0"})
        try:
            with urlopen(request, timeout=60) as response, temporary.open("wb") as output:
                shutil.copyfileobj(response, output)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            temporary.unlink(missing_ok=True)
            print(f"  [FAIL] {binary['role']}: {exc}", file=sys.stderr)
            return 1

        actual = sha256(temporary)
        if actual != expected:
            temporary.unlink(missing_ok=True)
            print(
                f"  [FAIL] {binary['role']}: expected {expected}, received {actual}",
                file=sys.stderr,
            )
            return 1
        temporary.replace(destination)
        print(f"  [ok]   {binary['role']}: {filename} {actual}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
