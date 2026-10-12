#!/usr/bin/env python3
"""Compute or verify this skill's deterministic canonical SHA-256.

README.md contains the canonical hash. To avoid a circular self-hash, the 64 hex characters
on the canonical-hash line are normalized to zeros before hashing. CHECKSUMS.sha256,
publication markers, caches, and compiled bytecode are excluded.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

HASH_PATTERN = re.compile(rb"(\*\*Canonical artifact SHA-256:\*\* `)[0-9a-fA-F]{64}(`)")
EXCLUDED_NAMES = {"CHECKSUMS.sha256", ".published", "_meta.json", "skill-card.md"}
EXCLUDED_PARTS = {".clawhub", "__pycache__", ".pytest_cache", ".ruff_cache",
                  ".mypy_cache", ".venv", ".tox", ".nox", ".git"}
CANONICAL_DUMMY = b"0000000000000000000000000000000000000000000000000000000000000000"


def root_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def included_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if path.name in EXCLUDED_NAMES:
            continue
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if path.suffix in {".pyc", ".pyo"}:
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(root).as_posix())


def normalized_content(path: Path) -> bytes:
    content = path.read_bytes()
    if path.name == "README.md":
        replaced, count = HASH_PATTERN.subn(rb"\g<1>" + CANONICAL_DUMMY + rb"\g<2>", content)
        if count != 1:
            raise RuntimeError("README.md must contain exactly one canonical artifact SHA-256 line.")
        return replaced
    return content


def canonical_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in included_files(root):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        content = normalized_content(path)
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def read_declared_hash(readme: Path) -> str:
    match = HASH_PATTERN.search(readme.read_bytes())
    if not match:
        raise RuntimeError("README.md does not contain a canonical artifact SHA-256.")
    return match.group(0).split(b"`")[1].decode("ascii").lower()


def write_declared_hash(readme: Path, value: str) -> None:
    content = readme.read_bytes()
    replacement = rb"\g<1>" + value.encode("ascii") + rb"\g<2>"
    updated, count = HASH_PATTERN.subn(replacement, content)
    if count != 1:
        raise RuntimeError("Could not update exactly one README canonical hash line.")
    readme.write_bytes(updated)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true",
                        help="Write the computed canonical hash into README.md, then verify it.")
    args = parser.parse_args()
    root = root_dir()
    readme = root / "README.md"
    computed = canonical_hash(root)
    if args.write:
        write_declared_hash(readme, computed)
        if canonical_hash(root) != computed:
            print("ERROR: canonical hash changed after README update", file=sys.stderr)
            return 1
    declared = read_declared_hash(readme)
    if declared != computed:
        print(f"FAIL declared={declared} computed={computed}", file=sys.stderr)
        return 1
    print(f"PASS canonical artifact SHA-256 {computed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
