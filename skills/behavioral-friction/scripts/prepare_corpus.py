#!/usr/bin/env python3
"""Prepare a Claude Code transcript corpus for behavioral-friction analysis.

Deterministic preprocessor (no model calls). Scans ~/.claude/projects, excludes
subagent/sidechain logs, sorts by modification time, and writes a stripped,
secret-redacted, session-tagged digest per session plus a manifest.json that
carries corpus-level counts the synthesis step needs (e.g. clean-session count).

Exit codes:
  0 - success, or --self-test passed
  1 - --self-test failed
  2 - usage / environment error
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_PROJECTS = Path.home() / ".claude" / "projects"
MAX_DIGEST_TOKENS = 4000
KEEP_HEAD = 5
KEEP_TAIL = 5

# Secret patterns: (label, regex, replacement). replacement=None replaces the
# whole match with <redacted:label>; a template string (e.g. r"\1=...") keeps a
# captured group so the key name survives. Mirrors the style of
# codebase-mapper/scripts/scan-secrets.py, plus env-style and header rules.
REDACTION_PATTERNS = [
    ("openai_or_stripe_key", re.compile(r"sk-[A-Za-z0-9]{20,}"), None),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), None),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"), None),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"), None),
    ("pem_private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), None),
    (
        "jwt",
        re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
        None,
    ),
    (
        "bearer_header",
        re.compile(r"(?i)\b(?:authorization|bearer)\b\s*[:=]?\s*[A-Za-z0-9._\-]{12,}"),
        None,
    ),
    (
        "env_secret",
        re.compile(
            r"""(?ix)
            \b([A-Z0-9_]*(?:KEY|SECRET|TOKEN|PASSWORD|PASSWD|CREDENTIAL)[A-Z0-9_]*)
            \s*[:=]\s*
            ["']?[^\s"']{6,}["']?
            """
        ),
        r"\1=<redacted:env_secret>",
    ),
]


def redact(text):
    if not text:
        return text
    for label, pattern, repl in REDACTION_PATTERNS:
        text = pattern.sub(repl if repl is not None else f"<redacted:{label}>", text)
    return text


def estimate_tokens(text):
    return len(text) // 4


def iso_date(ts):
    if isinstance(ts, str) and re.match(r"\d{4}-\d{2}-\d{2}", ts):
        return ts[:10]
    return None


def iter_jsonl(path):
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def extract_blocks(content):
    """Return (texts, tool_names) from a message.content value.

    tool_result blocks are intentionally dropped (payload stripping)."""
    texts, tools = [], []
    if isinstance(content, str):
        if content.strip():
            texts.append(content)
    elif isinstance(content, list):
        for block in content:
            if not isinstance(block, dict):
                continue
            btype = block.get("type")
            if btype == "text" and block.get("text", "").strip():
                texts.append(block["text"])
            elif btype == "tool_use":
                tools.append(block.get("name", "tool"))
    return texts, tools


def parse_records(records):
    """Build a session digest model from transcript record dicts.

    Returns {session_id, session_date, exchanges:[(role,text)]}. Sidechain
    records are skipped defensively; tool-result payloads are never collected.
    """
    session_id = None
    timestamps = []
    exchanges = []
    for rec in records:
        if not isinstance(rec, dict) or rec.get("isSidechain") is True:
            continue
        session_id = session_id or rec.get("sessionId")
        ts = rec.get("timestamp")
        if ts:
            timestamps.append(ts)
        rtype = rec.get("type")
        content = (rec.get("message") or {}).get("content")
        if rtype == "user":
            texts, _ = extract_blocks(content)
            exchanges.extend(("user", t) for t in texts)
        elif rtype == "assistant":
            texts, tools = extract_blocks(content)
            exchanges.extend(("assistant", t) for t in texts)
            exchanges.extend(("tool_use", name) for name in tools)
        elif rtype == "tool_use":  # defensive: top-level tool_use record shape
            _, tools = extract_blocks(content)
            exchanges.extend(("tool_use", name) for name in tools)
        # tool_result and metadata record types are dropped
    session_date = iso_date(min(timestamps)) if timestamps else None
    return {"session_id": session_id, "session_date": session_date, "exchanges": exchanges}


def format_exchange(role, text):
    text = " ".join(redact(text).split())
    if role == "tool_use":
        return f"[TOOL: {text}]"
    return f"{role.upper()}: {text}"


def build_digest(parsed):
    rendered = [format_exchange(role, text) for role, text in parsed["exchanges"]]
    full = "\n".join(rendered)
    if estimate_tokens(full) <= MAX_DIGEST_TOKENS:
        return full
    if len(rendered) <= KEEP_HEAD + KEEP_TAIL:
        return full[: MAX_DIGEST_TOKENS * 4]
    omitted = len(rendered) - KEEP_HEAD - KEEP_TAIL
    kept = rendered[:KEEP_HEAD] + [f"[... {omitted} exchanges omitted ...]"] + rendered[-KEEP_TAIL:]
    return "\n".join(kept)


def ym_key(s):
    y, m = s.split("-")
    return int(y) * 12 + int(m)


def scan(projects_dir):
    all_files = [p for p in projects_dir.rglob("*.jsonl") if p.is_file()]
    main = [p for p in all_files if "subagents" not in p.relative_to(projects_dir).parts]
    return all_files, main


def mtime_date(path):
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d")


def select(main_files, projects_dir, project, period, limit):
    files = sorted(main_files, key=lambda p: p.stat().st_mtime, reverse=True)
    if project:
        files = [p for p in files if project in p.relative_to(projects_dir).parts[0]]
    if period:
        lo, hi = ym_key(period[0]), ym_key(period[1])
        files = [
            p
            for p in files
            if lo <= ym_key(datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m")) <= hi
        ]
    return files[:limit]


def safe_name(value, fallback):
    base = value or fallback
    return re.sub(r"[^A-Za-z0-9_-]", "_", base)


def run(args):
    projects_dir = Path(args.projects_dir).expanduser()
    if not projects_dir.is_dir():
        print(f"error: projects dir not found: {projects_dir}", file=sys.stderr)
        return 2

    all_files, main_files = scan(projects_dir)
    selected = select(main_files, projects_dir, args.project, args.period, args.limit)
    dates = sorted(mtime_date(p) for p in selected) if selected else []
    date_range = [dates[0], dates[-1]] if dates else []

    corpus = {
        "total_jsonl": len(all_files),
        "subagent_excluded": len(all_files) - len(main_files),
        "main_sessions": len(main_files),
        "selected": len(selected),
        "date_range": date_range,
    }

    if args.dry_run:
        print(json.dumps({"corpus": corpus}, indent=2))
        return 0

    if not selected:
        print("No sessions matched the filters; nothing to analyze.", file=sys.stderr)
        return 0

    out_dir = Path(args.out).expanduser()
    sessions_dir = out_dir / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    sessions = []
    for path in selected:
        parsed = parse_records(iter_jsonl(path))
        sid = safe_name(parsed["session_id"], path.stem)
        digest_rel = f"sessions/{sid}.txt"
        (out_dir / digest_rel).write_text(build_digest(parsed), encoding="utf-8")
        sessions.append(
            {
                "session_id": parsed["session_id"] or path.stem,
                "session_date": parsed["session_date"] or mtime_date(path),
                "source": str(path),
                "digest_path": digest_rel,
                "exchanges": len(parsed["exchanges"]),
            }
        )

    manifest = {
        "generated": datetime.now().strftime("%Y-%m-%d"),
        "corpus": corpus,
        "sessions": sessions,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {len(sessions)} digests and manifest.json to {out_dir}")
    print(
        f"Corpus: {corpus['main_sessions']} main sessions "
        f"({corpus['subagent_excluded']} subagent logs excluded), "
        f"{corpus['selected']} selected."
    )
    return 0


def self_test():
    records = [
        {
            "type": "user",
            "sessionId": "test-sess",
            "timestamp": "2026-06-01T10:00:00Z",
            "message": {"role": "user", "content": "Please deploy with AWS_SECRET=AKIAIOSFODNN7EXAMPLE now"},
        },
        {
            "type": "assistant",
            "sessionId": "test-sess",
            "timestamp": "2026-06-01T10:00:05Z",
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Sure, running the build."},
                    {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "make"}},
                ],
            },
        },
        {
            "type": "user",
            "sessionId": "test-sess",
            "timestamp": "2026-06-01T10:00:09Z",
            "message": {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": "t1", "content": "BUILD_OUTPUT_SHOULD_BE_DROPPED", "is_error": False}
                ],
            },
        },
        {
            "type": "assistant",
            "isSidechain": True,
            "sessionId": "sub-1",
            "timestamp": "2026-06-01T10:00:10Z",
            "message": {"role": "assistant", "content": [{"type": "text", "text": "SIDECHAIN_SHOULD_BE_EXCLUDED"}]},
        },
    ]
    parsed = parse_records(records)
    digest = build_digest(parsed)
    checks = [
        ("user text extracted", "Please deploy" in digest),
        ("assistant text extracted", "Sure, running the build." in digest),
        ("tool name extracted", "Bash" in digest),
        ("tool_result payload dropped", "BUILD_OUTPUT_SHOULD_BE_DROPPED" not in digest),
        ("sidechain excluded", "SIDECHAIN_SHOULD_BE_EXCLUDED" not in digest),
        ("secret redacted", "AKIAIOSFODNN7EXAMPLE" not in digest and "<redacted:" in digest),
        ("session id parsed", parsed["session_id"] == "test-sess"),
        ("session date parsed", parsed["session_date"] == "2026-06-01"),
    ]
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    failed = [name for name, ok in checks if not ok]
    if failed:
        print(f"self-test FAILED: {len(failed)} check(s)")
        return 1
    print("self-test PASSED")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Prepare a transcript corpus for behavioral-friction analysis.")
    parser.add_argument("--period", nargs=2, metavar=("START", "END"), help="Filter sessions by YYYY-MM range (by mtime)")
    parser.add_argument("--project", help="Filter to project dirs whose name contains this substring")
    parser.add_argument("--limit", type=int, default=30, help="Max sessions to select (default 30)")
    parser.add_argument("--out", default="./.behavioral-friction", help="Output dir (default ./.behavioral-friction)")
    parser.add_argument("--projects-dir", default=str(DEFAULT_PROJECTS), help="Transcript root (default ~/.claude/projects)")
    parser.add_argument("--dry-run", action="store_true", help="Report corpus stats only; write nothing")
    parser.add_argument("--self-test", action="store_true", help="Run built-in parser/redaction checks and exit")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
