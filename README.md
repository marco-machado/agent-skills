# Agent Skills

A collection of skills for AI coding agents. Skills are packaged instructions and scripts that extend agent capabilities.

Skills follow the [Agent Skills](https://agentskills.io/) format.

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

### [caveman](skills/caveman/)

Respond in broken caveman-speak — short sentences, no filler, dropped articles.

**Use when:**
- User asks for caveman mode, caveman style, or broken English responses
- User wants a terse, action-first response register until told otherwise

**Features:**
- Style rules with examples (normal → caveman transforms)
- Preserves code, file paths, and tool output literally — only prose changes
- Explicit stop conditions to exit the mode

### [jira-fetch-ticket](skills/jira-fetch-ticket/)

Fetch a Jira ticket and produce a structured analysis document. See [setup and usage](skills/jira-fetch-ticket/README.md).

**Use when:**
- Starting work on a Jira ticket
- Needing full context on a Jira issue before implementing
- Analyzing acceptance criteria, linked issues, and codebase impact

**Features:**
- Accepts full ticket ID (`PROJ-123`) or just the number (`123`, inferred from git branch)
- Fetches ticket fields, comments, linked issues, subtasks, and dev status (branches, PRs)
- Checks for parent epic context if already fetched
- Scans the codebase for relevant files and surfaces code references
- Produces a structured `docs/jira-tickets/TICKET_KEY/TICKET_KEY.md` document

## Installation

```bash
npx skills add marco-machado/agent-skills
```

## Skill Structure

Skills live under `skills/` and each contains:
- `SKILL.md` - Instructions for the agent
- `scripts/` - Helper scripts for automation (optional)
- `references/` - Supporting documentation (optional)

## License

MIT
