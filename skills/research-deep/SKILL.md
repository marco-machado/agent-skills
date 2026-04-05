---
name: research-deep
description: >
  Execute deep research on every item in a research outline, producing structured JSON per item
  and a final markdown report. Use after running /research to generate an outline. Reads
  outline.yaml and fields.yaml, launches parallel research agents in batches, validates output,
  generates a consolidated report, and supports resume on interruption. Trigger when the user
  says "start deep research", "research these items", "run the deep phase", "fill in the
  fields for each item", or "generate the research report".
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch, Task
compatibility: Requires Python 3.8+ for the validation script. Requires web search access.
metadata:
  version: "1.0.0"
  author: marco-machado
---

# Research Deep — Batch Item Research

Read a research outline (`outline.yaml` + `fields.yaml`) produced by `/research`, then research each item in parallel batches, producing one structured JSON file per item and a final consolidated markdown report.

## Variables

| Variable | Source | Description |
|----------|--------|-------------|
| `{topic}` | `outline.yaml` | The `topic` field |
| `{outline_dir}` | Discovered | Directory containing `outline.yaml` and `fields.yaml` |
| `{output_dir}` | `outline.yaml` | `execution.output_dir` (default: `./results`) resolved relative to `{outline_dir}` |
| `{batch_size}` | `outline.yaml` | `execution.batch_size` — max parallel agents per batch |
| `{items_per_agent}` | `outline.yaml` | `execution.items_per_agent` — items assigned to each agent |
| `{fields_path}` | Derived | Absolute path to `{outline_dir}/fields.yaml` |
| `{item_name}` | Per item | The item's `name` field from `outline.yaml` |
| `{item_slug}` | Derived | Slugified item name: lowercase, spaces to underscores, strip non-alphanumeric except underscores, collapse consecutive underscores. E.g. "GitHub Copilot" becomes `github_copilot` |
| `{output_path}` | Derived | `{output_dir}/{item_slug}.json` |

## Step 1: Locate Outline

Search for `*/outline.yaml` in the current working directory.

- If **exactly one** is found: read it along with the sibling `fields.yaml`. Store the containing directory as `{outline_dir}`.
- If **multiple** are found: list them and ask the user which to use.
- If **none** found: tell the user to run `/research` first and stop.

Read both files. Extract the items list and execution config. Report to the user:
- Topic: `{topic}`
- Items count: N items
- Batch config: `{batch_size}` parallel agents, `{items_per_agent}` items each
- Output directory: `{output_dir}`

## Step 2: Resume Check

Check `{output_dir}` for existing `.json` files.

For each existing JSON file:
1. Parse the filename back to an item name (reverse the slug: `github_copilot.json` -> match against items list)
2. Run the validation script to check completeness:
   ```bash
   python3 scripts/validate_json.py -f {fields_path} -j {output_path}
   ```
3. If validation passes (exit code 0): mark the item as **completed** — skip it
4. If validation fails (exit code 1): mark the item as **incomplete** — include it in the run

Report resume status to the user:
- "Found N/{total} completed items. Resuming with {remaining} items."
- List the completed items so the user can verify

If all items are already completed, report this and stop.

## Step 3: Batch Execution

Partition the remaining items into batches:
- Each agent handles up to `{items_per_agent}` items
- Launch up to `{batch_size}` agents in parallel per batch

**Before launching each batch**, show the user which items are in this batch and ask for approval:
- "Batch {N}/{total_batches}: items [list]. Launch?"

For each agent, build the prompt from the template below. Preserve the structure and goals; only substitute the `{variables}`.

Read `references/web-search-guide.md` for search methodology guidance to include in the agent context.

**Sub-agent prompt template:**

```
## Task
Research the following item(s) and output structured JSON.

Topic: {topic}

### Items to Research
{for each item assigned to this agent:}
- name: {item_name}
  description: {item_description}
{end for}

## Field Definitions
Read the field definitions file to understand what data to collect for each item:
{fields_path}

Use all field categories and fields defined in that file. Each item gets its own JSON object with every field populated.

## Research Instructions
- Search for authoritative, current information on each item
- Use 2-3 search query variations per item
- Prefer official sources (project websites, documentation, release announcements)
- Cross-reference claims across multiple sources when possible
- Note publication dates — flag anything older than 12 months

## Output Format
For each item, write a JSON file to its output path:

{for each item:}
- {item_name} -> {output_path}
{end for}

Each JSON file must follow this structure:
```json
{
  "name": "{item_name}",
  "category_name": {
    "field_name": "value",
    "field_name": "value"
  },
  "another_category": {
    "field_name": "value"
  },
  "uncertain": ["field_name_1", "field_name_2"],
  "sources": [
    {"description": "Source description", "url": "https://..."}
  ]
}
```

### Field value rules:
- Populate every field defined in fields.yaml
- If a value cannot be confidently determined, write your best estimate and append "[uncertain]" to the string value
- Add the field name to the top-level "uncertain" array
- All values must be in English
- Use the detail_level from fields.yaml to calibrate response length:
  - brief: single value or short phrase
  - moderate: 1-3 sentences
  - detailed: full paragraph or structured breakdown

## Validation
After writing each JSON file, run:
```bash
python3 {validate_script_path} -f {fields_path} -j {output_path}
```
If validation fails, read the error output, fix the JSON, and re-run until it passes.
The task is complete only after all items pass validation.
```

**One-shot example** (single item, topic "AI Coding History"):
```
## Task
Research the following item(s) and output structured JSON.

Topic: AI Coding History

### Items to Research
- name: GitHub Copilot
  description: Developed by Microsoft/GitHub, first mainstream AI coding assistant

## Field Definitions
Read the field definitions file to understand what data to collect for each item:
/Users/you/ai-coding-history/fields.yaml

Use all field categories and fields defined in that file. Each item gets its own JSON object with every field populated.

## Research Instructions
- Search for authoritative, current information on each item
- Use 2-3 search query variations per item
- Prefer official sources (project websites, documentation, release announcements)
- Cross-reference claims across multiple sources when possible
- Note publication dates — flag anything older than 12 months

## Output Format
For each item, write a JSON file to its output path:

- GitHub Copilot -> /Users/you/ai-coding-history/results/github_copilot.json

Each JSON file must follow this structure:
```json
{
  "name": "GitHub Copilot",
  "basic_info": {
    "release_date": "2021-06-29",
    "company": "Microsoft / GitHub"
  },
  "technical_features": {
    "underlying_model": "OpenAI Codex (initially), GPT-4 (current)",
    "context_window": "Varies by tier; up to 128k tokens in Copilot Enterprise [uncertain]"
  },
  "uncertain": ["context_window"],
  "sources": [
    {"description": "GitHub Copilot official documentation", "url": "https://docs.github.com/copilot"}
  ]
}
```

### Field value rules:
- Populate every field defined in fields.yaml
- If a value cannot be confidently determined, write your best estimate and append "[uncertain]" to the string value
- Add the field name to the top-level "uncertain" array
- All values must be in English
- Use the detail_level from fields.yaml to calibrate response length:
  - brief: single value or short phrase
  - moderate: 1-3 sentences
  - detailed: full paragraph or structured breakdown

## Validation
After writing each JSON file, run:
```bash
python3 /Users/you/agent-skills/skills/research-deep/scripts/validate_json.py -f /Users/you/ai-coding-history/fields.yaml -j /Users/you/ai-coding-history/results/github_copilot.json
```
If validation fails, read the error output, fix the JSON, and re-run until it passes.
The task is complete only after all items pass validation.
```

## Step 4: Monitor and Continue

After launching a batch:

1. **Wait** for all agents in the batch to complete
2. **Collect results**: for each agent, check that its output JSON files exist and pass validation
3. **Handle failures**:
   - If an agent fails entirely (no output): log the item names and add them to a retry list
   - If validation fails after the agent finishes: log which fields are missing/invalid
   - **Retry failed items once** in the next batch. If they fail again, mark them as failed and move on.
4. **Report batch progress**: "Batch {N} complete: {succeeded}/{total} items succeeded."
5. **Launch next batch** (with user approval)

## Step 5: Summary Report

After all batches complete, output:

```
## Research Complete

**Topic**: {topic}
**Output directory**: {output_dir}

### Results
- Completed: {count} / {total} items
- Failed: {count} items {list names if any}
- Items with uncertain fields: {count}

### Uncertain Fields Summary
{For each item with uncertain fields:}
- {item_name}: {list of uncertain field names}
{end for}

### Failed Items
{If any:}
- {item_name}: {reason for failure}
{end for}
```

## Step 6: Generate Report

After Step 5's summary (or after resume finds all items already completed), generate a markdown report.

**Ask the user**: "Which fields should appear as summary columns in the table of contents? (Pick from the available fields — e.g. release_date, company, github_stars)"

To help the user choose, scan the completed JSON files and list fields that have short values (single numbers, dates, short strings) — these work well as TOC columns.

Run the report generation script:
```bash
python3 scripts/generate_report.py \
  -f {fields_path} \
  -d {output_dir} \
  -o {outline_dir}/report.md \
  --toc-fields field1,field2,field3
```

If the script exits with an error, show the error output to the user and stop.

Otherwise, confirm: "Report written to `{outline_dir}/report.md`" and show the first ~30 lines as a preview.

## Rules

- NEVER modify `outline.yaml` or `fields.yaml` — they are read-only inputs
- NEVER skip the user approval step before each batch
- NEVER retry a failed item more than once
- Always run the validation script after writing each JSON — do not mark an item as complete until validation passes
- Write JSON files atomically: write to `{output_path}.tmp` first, then rename to `{output_path}` after validation passes

## Gotchas

- **Slug collisions**: two items could slug to the same filename (e.g. "C++" and "C" could both become `c`). If detected, append a numeric suffix: `c.json`, `c_2.json`.
- **Large item counts**: if there are 50+ items, warn the user about total agent cost before starting.
- **fields.yaml changes**: if the user modifies fields.yaml between runs, previously completed items won't have the new fields. The validation script will catch this — those items will be re-researched on resume.
