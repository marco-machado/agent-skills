---
name: research
description: >
  Conduct preliminary research on a topic and generate a structured research outline.
  Use when the user says "research X", "compare options for X", "survey the landscape of X",
  "what are the main players in X", or needs a structured starting point for academic research,
  benchmark research, technology selection, or competitive analysis.
  Produces an outline.yaml (items + config) and fields.yaml (field definitions) that can
  feed into deeper research phases.
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, WebSearch, WebFetch, Task, AskUserQuestion
compatibility: Requires web search access for Step 2. Python 3.8+ if using companion scripts.
metadata:
  version: "1.0.0"
  author: marco-machado
args:
  - name: topic
    description: "The research topic (e.g. 'AI coding assistants', 'vector databases 2024')"
    required: true
---

# Research — Preliminary Outline

Generate a structured research outline for `{{topic}}`. The output is two YAML files — an items list and a field schema — ready for a deeper research phase.

## Variables

| Variable | Source | Description |
|----------|--------|-------------|
| `{topic}` | User argument | The research topic as provided |
| `{topic_slug}` | Derived | Slugified topic: lowercase, spaces to hyphens, strip non-alphanumeric except hyphens, collapse consecutive hyphens, trim leading/trailing hyphens. E.g. "AI Coding Tools (2024)" becomes `ai-coding-tools-2024` |
| `{date}` | System | Current date in `YYYY-MM-DD` format |
| `{step1_output}` | Step 1 | The initial framework (items list + field framework) in the format defined in Step 1 |
| `{step2_output}` | Step 2 | Supplementary items and fields from web search |
| `{time_range}` | User input | Time filter for web search (e.g. "last 6 months", "since 2024", "unlimited") |

## Step 1: Generate Initial Framework

Using your existing knowledge of `{topic}`, generate an initial framework with two sections:

**Required output format for `{step1_output}`:**

```
### Items List
1. Item Name: Brief description — why it's relevant to {topic}
2. Item Name: Brief description — why it's relevant to {topic}
...

### Field Framework
- Category Name: field_1, field_2, field_3
  - field_1: What this field captures
  - field_2: What this field captures
  - field_3: What this field captures
- Category Name: field_4, field_5
  ...
```

Aim for 10-30 items and 3-6 field categories depending on topic breadth.

**Present `{step1_output}` to the user and ask:**
1. Should any items be added or removed?
2. Does the field framework cover the right dimensions?
3. Any categories or fields to add/remove?

Incorporate feedback before proceeding.

## Step 2: Web Search Supplement

Ask the user: **"What time range should I search? (e.g. last 6 months, since 2024, unlimited)"** — store as `{time_range}`.

Launch a background research task using the following prompt. Preserve the structure and goals; only substitute the `{variables}`.

If `references/web-search-guide.md` is available, read it before executing searches for methodology guidance.

**Sub-agent prompt:**

```
## Task
Research topic: {topic}
Current date: {date}

Based on the following initial framework, supplement latest items and recommended research fields.

## Search Strategy
- Use 3-5 query variations (technical terms, brand names, common synonyms)
- Prioritize: official sources, reputable tech publications, academic papers (if applicable)
- Cross-reference findings across multiple sources
- Note publication dates — flag anything older than 12 months as potentially outdated

## Existing Framework
{step1_output}

## Goals
1. Verify if existing items are missing important entries
2. Supplement items for any gaps found
3. Search for {topic} related items within {time_range} and supplement
4. Suggest new field categories if the existing framework misses important dimensions

## Output Requirements
Return structured results directly (do not write files):

### Supplementary Items
- item_name: Brief explanation (why it should be added)
...

### Recommended Supplementary Fields
- field_name: Field description (why this dimension is needed)
...

### Sources
- [Source description](url)
...
```

**One-shot example** (topic: "AI Coding History"):
```
## Task
Research topic: AI Coding History
Current date: 2025-12-30

Based on the following initial framework, supplement latest items and recommended research fields.

## Search Strategy
- Use 3-5 query variations (technical terms, brand names, common synonyms)
- Prioritize: official sources, reputable tech publications, academic papers (if applicable)
- Cross-reference findings across multiple sources
- Note publication dates — flag anything older than 12 months as potentially outdated

## Existing Framework
### Items List
1. GitHub Copilot: Developed by Microsoft/GitHub, first mainstream AI coding assistant
2. Cursor: AI-first IDE, based on VSCode
...

### Field Framework
- Basic Info: name, release_date, company
  - name: Product or project name
  - release_date: Initial public release date
  - company: Developing company or organization
- Technical Features: underlying_model, context_window
  - underlying_model: The LLM powering the tool
  - context_window: Maximum context size supported
...

## Goals
1. Verify if existing items are missing important entries
2. Supplement items for any gaps found
3. Search for AI Coding History related items within since 2024 and supplement
4. Suggest new field categories if the existing framework misses important dimensions

## Output Requirements
Return structured results directly (do not write files):

### Supplementary Items
- item_name: Brief explanation (why it should be added)
...

### Recommended Supplementary Fields
- field_name: Field description (why this dimension is needed)
...

### Sources
- [Source description](url)
...
```

**Wait for the background task to complete** and store its output as `{step2_output}` before proceeding to Step 3.

**Edge cases:**
- If web search returns no useful results, proceed with Step 1 output only and note the gap to the user.
- If the topic is very broad, suggest the user narrow scope before searching.

## Step 3: Merge Existing Fields

Ask the user: **"Do you have an existing field definition file you'd like to merge? If so, provide the path."**

- If **yes**: read the file and merge with the current framework.
  - **Merge precedence**: user's existing definitions win on conflicts. If a field exists in both the generated framework and the user's file, keep the user's definition and description.
  - Add any new fields from Steps 1-2 that don't conflict.
- If **no**: proceed with the merged output from Steps 1 and 2.

## Step 4: Generate Output Files

Merge `{step1_output}`, `{step2_output}`, and any user-provided fields into two YAML files.

**outline.yaml** — items and execution config:

```yaml
topic: "{topic}"
date: "{date}"
items:
  - name: "Item Name"
    description: "Brief description"
  - name: "Item Name"
    description: "Brief description"
  # ... all items from Steps 1-2, deduplicated
execution:
  batch_size: 3       # number of parallel research agents in deep phase
  items_per_agent: 5  # items each agent handles
  output_dir: "./results"
sources:
  - description: "Source description"
    url: "https://..."
  # ... sources from Step 2
```

Ask the user to confirm `batch_size` and `items_per_agent`:
- **batch_size**: "How many parallel agents for the deep research phase? (default: 3)"
- **items_per_agent**: "How many items per agent? (default: 5)"

These control how `/research-deep` parallelizes work. Higher `batch_size` = faster but more resource-intensive.

**fields.yaml** — field definitions:

```yaml
topic: "{topic}"
categories:
  - name: "Category Name"
    fields:
      - name: "field_name"
        description: "What this field captures"
        detail_level: "brief"    # brief | moderate | detailed
      - name: "field_name"
        description: "What this field captures"
        detail_level: "moderate"
uncertain: []
# Reserved: auto-populated during deep research phase when a field
# value cannot be confidently determined. Always empty at outline stage.
```

**detail_level guidance:**
- `brief` — a single value or short phrase (e.g. company name, release date)
- `moderate` — 1-3 sentences explaining the item (e.g. technical approach, key differentiator)
- `detailed` — a full paragraph or structured breakdown (e.g. architecture overview, comparison notes)

Default to `brief` for factual fields, `moderate` for analytical fields. Only use `detailed` for fields the user explicitly wants depth on.

## Step 5: Save and Confirm

1. Create directory: `./{topic_slug}/`
2. Write `outline.yaml` and `fields.yaml` to that directory
3. Present both files to the user for review
4. Ask: "Does this look right? Any items or fields to adjust before deep research?"

**Output structure:**
```
{current_working_directory}/{topic_slug}/
  ├── outline.yaml    # items list + execution config
  └── fields.yaml     # field definitions
```

## Rules

- NEVER start the deep research — this skill produces the outline only
- NEVER modify files outside the `{topic_slug}/` output directory
- If unsure whether an item belongs in the list, include it and let the user prune
- Keep items deduplicated — if Step 2 finds something already in Step 1, skip it

## What's Next

The output files (`outline.yaml` + `fields.yaml`) are a self-contained research plan. They can be used to:
- **Add more items or fields** by editing the YAML files directly
- **Drive a deep research phase** where each item is researched individually and output as structured JSON
