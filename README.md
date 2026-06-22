# Agent Skills

A collection of skills for AI coding agents. Skills are packaged instructions and scripts that extend agent capabilities.

Skills follow the [Agent Skills](https://agentskills.io/) format.

## Installation

```bash
npx skills add marco-machado/agent-skills
```

> **Better alternative (separate tool):** [`gh skill install`](https://cli.github.com/manual/gh_skill_install) — GitHub CLI's first-party agent skills installer (v2.90.0+). It supports 40+ host-aware install paths, version pinning, integrity checks, and writes provenance metadata into each `SKILL.md`. Requires a separate install of the GitHub CLI. Once that's available:
>
> ```bash
> gh skill install marco-machado/agent-skills <skill-name>
> ```

## Available Skills

### [agent-skills](skills/agent-skills/)

Create agent skills following the agentskills open format.

**Use when:**
- Creating a new skill from scratch
- Converting a workflow or runbook into a reusable skill
- Validating or improving an existing SKILL.md

**Features:**
- Full agentskills format spec and frontmatter constraints
- Best practices for writing effective skill instructions
- Validation script to check name, description, and structure
- References for eval workflow and description optimization

### [research](skills/research/)

Conduct preliminary research on a topic and generate a structured outline.

**Use when:**
- Starting research on a new topic (technology survey, competitive analysis, academic review)
- Needing a structured list of items and fields before diving deep

**Features:**
- Interactive framework generation with web search augmentation
- Produces `outline.yaml` (items + execution config) and `fields.yaml` (field schema)
- Supports merging with existing field definitions
- Self-contained web search methodology guide

### [research-deep](skills/research-deep/)

Execute deep research on every item in an outline, producing structured JSON and a markdown report.

**Use when:**
- You have an `outline.yaml` + `fields.yaml` (from `/research` or hand-crafted)
- You need detailed, structured data on each item in the outline

**Features:**
- Parallel batch execution with configurable concurrency
- Resume support — skips already-completed items on re-run
- Bundled validation script checks JSON output against field schema
- Generates a consolidated markdown report with table of contents
- Handles uncertain values, extra fields, and slug collisions

### [codebase-mapper](skills/codebase-mapper/)

Map a codebase by sequentially analyzing four focus areas (`tech`, `arch`, `quality`, `concerns`) and emit structured analysis docs to `docs/generated/`.

**Use when:**
- Starting work in an unfamiliar repo and needing a fast structural map
- Generating onboarding documentation (stack, architecture, conventions, concerns)
- Refreshing existing mapping docs after large changes

**Features:**
- Sequential focus phases — runs in any agentskills.io-compliant host, no host-specific extensions
- Refresh / Update / Abort gate when `docs/generated/` already exists
- Update mode lets the user re-run only selected focus areas
- Bundled secrets scanner runs over the generated docs and warns on potential leaks
- Per-focus exploration commands and document templates live in `references/`

### [behavioral-friction](skills/behavioral-friction/)

Analyze Claude Code session transcripts for behavioral friction and propose durable CLAUDE.md rules.

**Use when:**
- Improving your CLAUDE.md from real session behavior rather than guesswork
- Finding recurring interaction patterns (premature execution, scope creep, ignored preferences)
- Auditing where the model keeps misreading your intent

**Features:**
- Deterministic Python preprocessor scans `~/.claude/projects`, excludes subagent logs, strips tool payloads, and redacts secrets before analysis
- Per-session extraction via parallel Task subagents, classified against an 8-category behavioral taxonomy
- Confidence scored by distinct-session recurrence, so one noisy session can't inflate a pattern
- Outputs a report with evidence-backed, copy-pasteable CLAUDE.md rules

## License

MIT
