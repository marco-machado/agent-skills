#!/usr/bin/env python3
"""
Validate an Agent Skills skill directory.

Usage:
    python scripts/validate.py <path-to-skill-dir>
    python scripts/validate.py .   # validate the current directory

Exit codes:
    0 - valid
    1 - validation errors found
    2 - usage error
"""

import re
import sys
from pathlib import Path

NAME_PATTERN = re.compile(r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?$')
MAX_NAME_LEN = 64
MAX_DESC_LEN = 1024
MAX_COMPAT_LEN = 500


def parse_frontmatter(skill_md: str) -> tuple[dict, list[str]]:
    """Parse YAML frontmatter from SKILL.md. Returns (fields, errors)."""
    errors = []
    fields = {}

    lines = skill_md.splitlines()
    if not lines or lines[0].strip() != '---':
        errors.append("SKILL.md must start with '---' (YAML frontmatter)")
        return fields, errors

    end = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == '---':
            end = i
            break

    if end is None:
        errors.append("Frontmatter not closed — missing closing '---'")
        return fields, errors

    # Simple key: value parser (handles multi-line with >)
    current_key = None
    current_value = []
    in_block = False

    for line in lines[1:end]:
        if line and not line[0].isspace():
            if current_key:
                fields[current_key] = ' '.join(current_value).strip().lstrip('> ')
            match = re.match(r'^(\w[\w-]*):\s*(.*)', line)
            if match:
                current_key = match.group(1)
                val = match.group(2).strip()
                if val == '>':
                    current_value = []
                    in_block = True
                else:
                    current_value = [val]
                    in_block = False
            else:
                current_key = None
                current_value = []
        elif current_key and line.strip():
            current_value.append(line.strip())

    if current_key:
        fields[current_key] = ' '.join(current_value).strip().lstrip('> ')

    return fields, errors


def validate_skill(skill_dir: Path) -> list[str]:
    errors = []
    warnings = []

    skill_md_path = skill_dir / 'SKILL.md'
    if not skill_md_path.exists():
        errors.append(f"Missing required file: SKILL.md")
        return errors

    content = skill_md_path.read_text(encoding='utf-8')
    fields, parse_errors = parse_frontmatter(content)
    errors.extend(parse_errors)

    if parse_errors:
        return errors

    # Validate name
    name = fields.get('name', '').strip()
    if not name:
        errors.append("'name' field is required")
    else:
        if len(name) > MAX_NAME_LEN:
            errors.append(f"'name' exceeds {MAX_NAME_LEN} characters (got {len(name)})")
        if not NAME_PATTERN.match(name):
            errors.append(
                f"'name' must contain only lowercase letters, numbers, and hyphens; "
                f"must not start/end with a hyphen or contain consecutive hyphens. Got: '{name}'"
            )
        if '--' in name:
            errors.append(f"'name' must not contain consecutive hyphens: '{name}'")
        dir_name = skill_dir.name
        if name != dir_name:
            errors.append(
                f"'name' field ('{name}') must match directory name ('{dir_name}')"
            )

    # Validate description
    desc = fields.get('description', '').strip()
    if not desc:
        errors.append("'description' field is required")
    else:
        if len(desc) > MAX_DESC_LEN:
            errors.append(
                f"'description' exceeds {MAX_DESC_LEN} characters (got {len(desc)})"
            )
        if len(desc) < 20:
            warnings.append("'description' seems very short — it's the primary trigger mechanism")

    # Validate compatibility if present
    compat = fields.get('compatibility', '').strip()
    if compat and len(compat) > MAX_COMPAT_LEN:
        errors.append(
            f"'compatibility' exceeds {MAX_COMPAT_LEN} characters (got {len(compat)})"
        )

    # Check body content
    lines = content.splitlines()
    body_start = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == '---':
            body_start = i + 1
            break

    if body_start is not None:
        body_lines = lines[body_start:]
        if not any(l.strip() for l in body_lines):
            warnings.append("SKILL.md body is empty — add instructions for the agent")
        line_count = len(body_lines)
        if line_count > 500:
            warnings.append(
                f"SKILL.md body is {line_count} lines (recommended: under 500). "
                "Consider moving detailed content to references/"
            )

    # Print results
    if errors:
        print(f"❌ {skill_dir} — {len(errors)} error(s), {len(warnings)} warning(s)")
        for e in errors:
            print(f"  ERROR: {e}")
        for w in warnings:
            print(f"  WARN:  {w}")
    elif warnings:
        print(f"⚠️  {skill_dir} — valid with {len(warnings)} warning(s)")
        for w in warnings:
            print(f"  WARN:  {w}")
    else:
        print(f"✅ {skill_dir} — valid")
        if name:
            print(f"  name: {name}")
        if desc:
            preview = desc[:80] + "..." if len(desc) > 80 else desc
            print(f"  description: {preview}")

    return errors


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)

    skill_dir = Path(sys.argv[1]).resolve()

    if not skill_dir.exists():
        print(f"Error: directory not found: {skill_dir}", file=sys.stderr)
        sys.exit(2)

    if not skill_dir.is_dir():
        print(f"Error: not a directory: {skill_dir}", file=sys.stderr)
        sys.exit(2)

    errors = validate_skill(skill_dir)
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
