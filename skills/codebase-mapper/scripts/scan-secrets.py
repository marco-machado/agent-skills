#!/usr/bin/env python3
"""Scan markdown files for accidentally-leaked secrets.

Walks *.md files under the given directory and reports lines matching
common secret patterns (cloud keys, OAuth tokens, JWTs, PEM private
keys, generic API_KEY/SECRET/PASSWORD/TOKEN assignments).

Exit codes:
  0 - no hits
  1 - one or more hits
  2 - usage error
"""

import argparse
import re
import sys
from pathlib import Path

PATTERNS = [
    ("openai_or_stripe", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("pem_private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    (
        "jwt",
        re.compile(
            r"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\b"
        ),
    ),
    (
        "generic_credential",
        re.compile(
            r"""(?ix)
            (api[_-]?key|secret|password|token|bearer)
            \s*[:=]\s*
            ["'][^"'\s]{8,}["']
            """
        ),
    ),
]


def truncate(s: str, n: int = 60) -> str:
    s = s.strip()
    return s if len(s) <= n else s[: n - 1] + "..."


def scan_file(path: Path):
    hits = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for lineno, line in enumerate(f, start=1):
                for name, pattern in PATTERNS:
                    m = pattern.search(line)
                    if m:
                        hits.append((path, lineno, name, truncate(m.group(0))))
                        break
    except OSError as e:
        print(f"warn: cannot read {path}: {e}", file=sys.stderr)
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan markdown files for accidentally-leaked secrets.",
        epilog=(
            "Examples:\n"
            "  scan-secrets.py docs/generated/\n"
            "  scan-secrets.py path/to/dir"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default="docs/generated",
        help="Directory to scan (default: docs/generated)",
    )
    args = parser.parse_args()

    root = Path(args.directory)
    if not root.exists():
        print(f"error: directory not found: {root}", file=sys.stderr)
        return 2
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    md_files = sorted(root.rglob("*.md"))
    if not md_files:
        print(f"warn: no *.md files under {root}", file=sys.stderr)
        return 0

    all_hits = []
    for path in md_files:
        all_hits.extend(scan_file(path))

    for path, lineno, name, excerpt in all_hits:
        print(f"{path}:{lineno}:{name}:{excerpt}")

    return 1 if all_hits else 0


if __name__ == "__main__":
    sys.exit(main())
