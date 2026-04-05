#!/usr/bin/env python3
"""
Validate a research output JSON file against a fields.yaml schema.

Checks that every field defined in fields.yaml is present in the JSON output
and that values are non-empty. Reports missing fields, empty values, and
uncertain markings.

Usage:
    python scripts/validate_json.py -f fields.yaml -j output.json

Exit codes:
    0 - valid (all fields present and non-empty)
    1 - validation errors found
    2 - usage error (bad args, missing files, parse errors)
"""

import argparse
import json
import sys
from pathlib import Path


def parse_fields_yaml(path: Path) -> tuple[list[tuple[str, str]], str | None]:
    """
    Minimal YAML parser for fields.yaml.
    Returns ([(category, field_name), ...], error_message | None).

    Expects structure:
        categories:
          - name: "Category"
            fields:
              - name: "field_name"
                ...
    """
    fields = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    current_category = None

    # Strategy: use indentation to distinguish category-level vs field-level
    # entries. In the expected YAML structure:
    #   categories:           (indent 0)
    #     - name: "Cat"       (indent 2-4, category)
    #       fields:           (indent 4-6)
    #         - name: "fld"   (indent 6+, field)
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())

        if stripped.startswith("- name:"):
            val = stripped.split(":", 1)[1].strip().strip('"').strip("'")
            if indent <= 5:
                # Category-level name
                current_category = val
            else:
                # Field-level name
                if current_category and val:
                    fields.append((current_category, val))

    if not fields:
        return fields, "No fields found in fields.yaml — check the file format"

    return fields, None


def validate_json_against_fields(
    json_data: dict,
    fields: list[tuple[str, str]],
) -> tuple[list[str], list[str], list[str]]:
    """
    Validate JSON data against expected fields.
    Returns (errors, warnings, info).
    """
    errors = []
    warnings = []
    info = []

    uncertain = json_data.get("uncertain", [])
    if not isinstance(uncertain, list):
        errors.append("'uncertain' field must be a list")
        uncertain = []

    for category, field_name in fields:
        cat_data = json_data.get(category)
        if cat_data is None:
            errors.append(f"Missing category: '{category}'")
            continue
        if not isinstance(cat_data, dict):
            errors.append(f"Category '{category}' must be an object, got {type(cat_data).__name__}")
            continue

        value = cat_data.get(field_name)
        if value is None:
            errors.append(f"Missing field: '{category}.{field_name}'")
        elif isinstance(value, str) and not value.strip():
            errors.append(f"Empty value: '{category}.{field_name}'")
        elif isinstance(value, str) and "[uncertain]" in value:
            if field_name not in uncertain:
                warnings.append(
                    f"Field '{field_name}' is marked [uncertain] in value "
                    f"but not listed in the uncertain array"
                )

    for field_name in uncertain:
        found = False
        for category, fname in fields:
            if fname == field_name:
                cat_data = json_data.get(category, {})
                if isinstance(cat_data, dict) and field_name in cat_data:
                    found = True
                    break
        if not found:
            warnings.append(
                f"Field '{field_name}' is in the uncertain array "
                f"but was not found in the output"
            )

    if "sources" not in json_data:
        warnings.append("No 'sources' array — consider adding source references")
    elif not json_data["sources"]:
        warnings.append("'sources' array is empty")
    else:
        info.append(f"Sources: {len(json_data['sources'])} references")

    info.append(f"Uncertain fields: {len(uncertain)}")

    return errors, warnings, info


def main():
    parser = argparse.ArgumentParser(
        description="Validate research output JSON against fields.yaml"
    )
    parser.add_argument(
        "-f", "--fields", required=True, help="Path to fields.yaml"
    )
    parser.add_argument(
        "-j", "--json", required=True, help="Path to output JSON file"
    )
    args = parser.parse_args()

    fields_path = Path(args.fields)
    json_path = Path(args.json)

    if not fields_path.exists():
        print(f"Error: fields file not found: {fields_path}", file=sys.stderr)
        sys.exit(2)

    if not json_path.exists():
        print(f"Error: JSON file not found: {json_path}", file=sys.stderr)
        sys.exit(2)

    fields, parse_error = parse_fields_yaml(fields_path)
    if parse_error:
        print(f"Error parsing fields.yaml: {parse_error}", file=sys.stderr)
        sys.exit(2)

    try:
        json_data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        sys.exit(2)

    if not isinstance(json_data, dict):
        print("Error: JSON root must be an object", file=sys.stderr)
        sys.exit(2)

    errors, warnings, info = validate_json_against_fields(json_data, fields)

    if errors:
        print(f"FAIL — {len(errors)} error(s), {len(warnings)} warning(s)")
        for e in errors:
            print(f"  ERROR: {e}")
        for w in warnings:
            print(f"  WARN:  {w}")
        sys.exit(1)
    elif warnings:
        print(f"PASS with {len(warnings)} warning(s)")
        for w in warnings:
            print(f"  WARN:  {w}")
        for i in info:
            print(f"  INFO:  {i}")
        sys.exit(0)
    else:
        print(f"PASS — all {len(fields)} fields validated")
        for i in info:
            print(f"  INFO:  {i}")
        sys.exit(0)


if __name__ == "__main__":
    main()
