#!/usr/bin/env python3
"""Compare matching files in two Microsoft KB file-information manifests."""

from __future__ import annotations

import argparse
import csv
import fnmatch
import json
import sys
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path


DEFAULT_BEFORE_URL = (
    "https://download.microsoft.com/download/"
    "d152e49d-8ff9-4132-b801-8d5acd69df40/5089573.csv"
)
DEFAULT_AFTER_URL = (
    "https://download.microsoft.com/download/"
    "6eef86cf-0ee7-47e3-9ec1-570504b20ebe/5094126.csv"
)


@dataclass(frozen=True)
class Entry:
    section: str
    filename: str
    version: str
    date: str
    time: str
    size: str
    sha1: str = ""
    sha256: str = ""

    def comparison_key(self) -> tuple[str, str]:
        # KB5089573 does not publish hashes, so compare the fields common to both manifests.
        return (self.version, self.size)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Download two official KB file manifests and compare matching Windows binaries."
        )
    )
    parser.add_argument("--before-kb", default="5089573")
    parser.add_argument("--before-url", default=DEFAULT_BEFORE_URL)
    parser.add_argument("--after-kb", default="5094126")
    parser.add_argument("--after-url", default=DEFAULT_AFTER_URL)
    parser.add_argument(
        "--pattern",
        default="dhcp*.dll",
        help="case-insensitive filename glob (default: dhcp*.dll)",
    )
    parser.add_argument(
        "--section",
        default="Windows 11, version 24H2 LCU x64-based",
        help="manifest section to compare",
    )
    parser.add_argument(
        "--build",
        default="26100",
        help="require file versions from this Windows build branch",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("artifacts/patch-tuesday/kb-manifests"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/patch-tuesday/kb-manifest-comparison.json"),
    )
    parser.add_argument("--refresh", action="store_true")
    return parser.parse_args()


def download(url: str, destination: Path, refresh: bool) -> None:
    if destination.is_file() and not refresh:
        print(f"using cached manifest: {destination}")
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "CLEARSECLABS-RITSEC/1.0"})
    print(f"downloading: {url}")
    with urllib.request.urlopen(request, timeout=60) as response:
        destination.write_bytes(response.read())
    print(f"saved:       {destination}")


def read_manifest(path: Path) -> list[Entry]:
    entries: list[Entry] = []
    section = ""

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            if not line.startswith('"'):
                section = line
                continue

            row = next(csv.reader([line]))
            if not row or row[0].casefold() == "file name" or len(row) < 5:
                continue
            values = row + [""] * (7 - len(row))
            entries.append(
                Entry(
                    section=section,
                    filename=values[0],
                    version=values[1],
                    date=values[2],
                    time=values[3],
                    size=values[4],
                    sha1=values[5],
                    sha256=values[6],
                )
            )
    return entries


def select(
    entries: list[Entry], pattern: str, section: str, build: str
) -> dict[str, list[Entry]]:
    selected: dict[str, list[Entry]] = {}
    version_prefix = f"10.0.{build}." if build else ""
    for entry in entries:
        if entry.section.casefold() != section.casefold():
            continue
        if not fnmatch.fnmatch(entry.filename.casefold(), pattern.casefold()):
            continue
        if version_prefix and not entry.version.startswith(version_prefix):
            continue
        selected.setdefault(entry.filename.casefold(), []).append(entry)
    return selected


def summarize(entries: list[Entry]) -> str:
    return "; ".join(
        f"{entry.version} ({entry.size} bytes)"
        for entry in sorted(entries, key=lambda item: item.comparison_key())
    ) or "not present"


def main() -> int:
    args = parse_args()
    before_path = args.cache_dir / f"KB{args.before_kb}.csv"
    after_path = args.cache_dir / f"KB{args.after_kb}.csv"

    download(args.before_url, before_path, args.refresh)
    download(args.after_url, after_path, args.refresh)

    before = select(read_manifest(before_path), args.pattern, args.section, args.build)
    after = select(read_manifest(after_path), args.pattern, args.section, args.build)
    filenames = sorted(set(before) | set(after))
    if not filenames:
        print("no matching files found", file=sys.stderr)
        return 2

    comparisons = []
    print()
    print(f"section: {args.section}")
    print(f"filter:  {args.pattern} on build branch {args.build}")
    print()
    print(f"{'file':<22} {'before':<37} {'after':<37} changed")
    print(f"{'-' * 22} {'-' * 37} {'-' * 37} {'-' * 7}")
    for filename in filenames:
        old_entries = before.get(filename, [])
        new_entries = after.get(filename, [])
        old_keys = {entry.comparison_key() for entry in old_entries}
        new_keys = {entry.comparison_key() for entry in new_entries}
        changed = old_keys != new_keys
        print(
            f"{filename:<22} {summarize(old_entries):<37} "
            f"{summarize(new_entries):<37} {'YES' if changed else 'no'}"
        )
        comparisons.append(
            {
                "filename": filename,
                "changed": changed,
                "comparison_basis": ["file_version", "file_size"],
                "before": [asdict(entry) for entry in old_entries],
                "after": [asdict(entry) for entry in new_entries],
            }
        )

    result = {
        "before": {"kb": f"KB{args.before_kb}", "url": args.before_url},
        "after": {"kb": f"KB{args.after_kb}", "url": args.after_url},
        "section": args.section,
        "build": args.build,
        "pattern": args.pattern,
        "comparisons": comparisons,
        "note": (
            "KB5089573 omits hashes. Change detection therefore compares file version and size; "
            "use Winbindex and downloaded-file SHA-256 values to select and verify the exact pair."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print()
    print(f"saved comparison: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
