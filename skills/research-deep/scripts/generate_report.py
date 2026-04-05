#!/usr/bin/env python3
"""
Generate a markdown report from research JSON results and a fields.yaml schema.

Reads all JSON files from the results directory, organizes them by the field
categories defined in fields.yaml, and produces a single markdown report with
a table of contents and detailed per-item sections.

Usage:
    python scripts/generate_report.py -f fields.yaml -d results/ -o report.md
    python scripts/generate_report.py -f fields.yaml -d results/ -o report.md --toc-fields release_date,company

Exit codes:
    0 - report generated successfully
    1 - error during generation
    2 - usage error (bad args, missing files)
"""

import argparse
import json
import re
import sys
from pathlib import Path


def parse_fields_yaml(path: Path) -> list[dict]:
    """
    Minimal YAML parser for fields.yaml.
    Returns list of {"name": category_name, "fields": [field_name, ...]}.
    """
    categories = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    current_category = None
    current_fields = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())

        if stripped.startswith("- name:"):
            val = stripped.split(":", 1)[1].strip().strip('"').strip("'")
            if indent <= 5:
                if current_category:
                    categories.append({"name": current_category, "fields": current_fields})
                current_category = val
                current_fields = []
            else:
                current_fields.append(val)

    if current_category:
        categories.append({"name": current_category, "fields": current_fields})

    return categories


def slugify_anchor(name: str) -> str:
    """Convert a name to a markdown anchor slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def resolve_field_value(item_data: dict, field_name: str, category_name: str) -> object:
    """
    Look up a field value in the JSON data. Supports both flat and nested structures.
    Search order: category dict -> top level -> traverse all nested dicts.
    """
    cat_key = slugify_key(category_name)
    cat_data = item_data.get(category_name) or item_data.get(cat_key)
    if isinstance(cat_data, dict) and field_name in cat_data:
        return cat_data[field_name]

    if field_name in item_data:
        return item_data[field_name]

    for val in item_data.values():
        if isinstance(val, dict) and field_name in val:
            return val[field_name]

    return None


def slugify_key(name: str) -> str:
    """Convert a category name to its likely JSON key form."""
    return re.sub(r"[^\w]+", "_", name.lower()).strip("_")


def is_uncertain(item_data: dict, field_name: str, value: object) -> bool:
    """Check if a field value should be skipped due to uncertainty."""
    if value is None:
        return True
    if isinstance(value, str):
        if not value.strip():
            return True
        if "[uncertain]" in value:
            return True
    uncertain_list = item_data.get("uncertain", [])
    if isinstance(uncertain_list, list) and field_name in uncertain_list:
        return True
    return False


def format_value(value: object) -> str:
    """Format a field value for markdown display."""
    if isinstance(value, list):
        if not value:
            return "*None*"
        if all(isinstance(v, dict) for v in value):
            lines = []
            for v in value:
                parts = [f"{k}: {v2}" for k, v2 in v.items()]
                lines.append("  - " + " | ".join(parts))
            return "\n" + "\n".join(lines)
        if len(value) <= 5 and all(isinstance(v, str) and len(v) < 50 for v in value):
            return ", ".join(str(v) for v in value)
        lines = ["  - " + str(v) for v in value]
        return "\n" + "\n".join(lines)

    if isinstance(value, dict):
        parts = [f"{k}: {v}" for k, v in value.items()]
        if len(parts) <= 3:
            return "; ".join(parts)
        lines = ["  - " + p for p in parts]
        return "\n" + "\n".join(lines)

    text = str(value)
    if len(text) > 150:
        return f"\n  > {text}"
    return text


def format_field_name(name: str) -> str:
    """Convert a snake_case field name to Title Case for display."""
    return name.replace("_", " ").title()


def generate_report(
    categories: list[dict],
    items: list[dict],
    toc_fields: list[str],
) -> str:
    """Generate the full markdown report."""
    lines = []

    # Title
    topic = ""
    if items:
        for item in items:
            if "topic" in item.get("_meta", {}):
                topic = item["_meta"]["topic"]
                break
    if not topic:
        topic = "Research Report"

    lines.append(f"# {topic}")
    lines.append("")

    # Table of Contents
    lines.append("## Table of Contents")
    lines.append("")

    for i, item in enumerate(items, 1):
        name = item.get("name", f"Item {i}")
        anchor = slugify_anchor(name)
        summary_parts = []
        for tf in toc_fields:
            val = resolve_field_value(item, tf, "")
            if val is not None and not is_uncertain(item, tf, val):
                display_val = str(val)
                if len(display_val) > 60:
                    display_val = display_val[:57] + "..."
                summary_parts.append(f"{format_field_name(tf)}: {display_val}")
        suffix = ""
        if summary_parts:
            suffix = " — " + " | ".join(summary_parts)
        lines.append(f"{i}. [{name}](#{anchor}){suffix}")

    lines.append("")

    # Detailed sections
    lines.append("---")
    lines.append("")

    known_internal_keys = {"name", "uncertain", "sources", "_meta", "_source_file"}

    for item in items:
        name = item.get("name", "Unknown")
        lines.append(f"## {name}")
        lines.append("")

        # Render each category from the schema
        rendered_fields = set()
        for category in categories:
            cat_name = category["name"]
            cat_fields = category["fields"]

            cat_lines = []
            for field_name in cat_fields:
                value = resolve_field_value(item, field_name, cat_name)
                if is_uncertain(item, field_name, value):
                    continue
                rendered_fields.add(field_name)
                formatted = format_value(value)
                cat_lines.append(f"- **{format_field_name(field_name)}**: {formatted}")

            if cat_lines:
                lines.append(f"### {cat_name}")
                lines.append("")
                lines.extend(cat_lines)
                lines.append("")

        # Extra fields not in schema
        extra_lines = []
        all_flat_keys = set()
        for key, val in item.items():
            if key in known_internal_keys:
                continue
            if isinstance(val, dict):
                for subkey, subval in val.items():
                    if subkey not in rendered_fields and not is_uncertain(item, subkey, subval):
                        rendered_fields.add(subkey)
                        formatted = format_value(subval)
                        extra_lines.append(f"- **{format_field_name(subkey)}**: {formatted}")
            else:
                all_flat_keys.add(key)
                if key not in rendered_fields and not is_uncertain(item, key, val):
                    rendered_fields.add(key)
                    formatted = format_value(val)
                    extra_lines.append(f"- **{format_field_name(key)}**: {formatted}")

        if extra_lines:
            lines.append("### Other Info")
            lines.append("")
            lines.extend(extra_lines)
            lines.append("")

        # Sources
        sources = item.get("sources", [])
        if sources:
            lines.append("### Sources")
            lines.append("")
            for src in sources:
                if isinstance(src, dict):
                    desc = src.get("description", "Source")
                    url = src.get("url", "")
                    if url:
                        lines.append(f"- [{desc}]({url})")
                    else:
                        lines.append(f"- {desc}")
                else:
                    lines.append(f"- {src}")
            lines.append("")

        # Uncertain fields
        uncertain = item.get("uncertain", [])
        if uncertain:
            lines.append("### Uncertain Fields")
            lines.append("")
            for field_name in uncertain:
                lines.append(f"- {format_field_name(field_name)}")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate markdown report from research JSON results"
    )
    parser.add_argument(
        "-f", "--fields", required=True, help="Path to fields.yaml"
    )
    parser.add_argument(
        "-d", "--data-dir", required=True, help="Path to results directory containing JSON files"
    )
    parser.add_argument(
        "-o", "--output", required=True, help="Output path for the markdown report"
    )
    parser.add_argument(
        "--toc-fields", default="", help="Comma-separated field names to show in table of contents"
    )
    args = parser.parse_args()

    fields_path = Path(args.fields)
    data_dir = Path(args.data_dir)
    output_path = Path(args.output)

    if not fields_path.exists():
        print(f"Error: fields file not found: {fields_path}", file=sys.stderr)
        sys.exit(2)

    if not data_dir.exists() or not data_dir.is_dir():
        print(f"Error: data directory not found: {data_dir}", file=sys.stderr)
        sys.exit(2)

    categories = parse_fields_yaml(fields_path)
    if not categories:
        print("Error: no categories found in fields.yaml", file=sys.stderr)
        sys.exit(1)

    toc_fields = [f.strip() for f in args.toc_fields.split(",") if f.strip()]

    json_files = sorted(data_dir.glob("*.json"))
    if not json_files:
        print(f"Error: no JSON files found in {data_dir}", file=sys.stderr)
        sys.exit(1)

    items = []
    for jf in json_files:
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data["_source_file"] = jf.name
                items.append(data)
            else:
                print(f"Warning: skipping {jf.name} — root is not an object", file=sys.stderr)
        except json.JSONDecodeError as e:
            print(f"Warning: skipping {jf.name} — {e}", file=sys.stderr)

    if not items:
        print("Error: no valid JSON items found", file=sys.stderr)
        sys.exit(1)

    items.sort(key=lambda x: x.get("name", ""))

    report = generate_report(categories, items, toc_fields)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    print(f"Report generated: {output_path}")
    print(f"  Items: {len(items)}")
    print(f"  Categories: {len(categories)}")
    if toc_fields:
        print(f"  TOC fields: {', '.join(toc_fields)}")


if __name__ == "__main__":
    main()
