---
name: agent-skills
description: >
  Use this skill any time the user wants to create, write, scaffold, or improve an Agent Skill
  following the agentskills open format (agentskills.io / github.com/agentskills/agentskills).
  Trigger when the user says "create a skill", "make a skill for X", "write a SKILL.md",
  "package this as a skill", "turn this workflow into a skill", "add a skill to this repo",
  or "I want to build a skill". Also trigger when the user wants to validate an existing
  SKILL.md, restructure a skill directory, or understand how to publish/share a skill.
  Use even if they don't explicitly mention "agentskills" or the open format.
compatibility: Works in any environment. Validation script requires Python 3.8+.
---

# Agent Skills — Open Format

A skill is a folder of instructions, scripts, and resources that an AI agent can
discover and use. Write once, use everywhere.

```
skill-name/
├── SKILL.md          # Required: metadata + instructions
├── scripts/          # Optional: executable code
├── references/       # Optional: documentation loaded on demand
└── assets/           # Optional: templates, images, data files
```

## Workflow

1. **Capture intent** — understand what the skill enables and when it should activate
2. **Interview** — ask about edge cases, inputs/outputs, dependencies, success criteria
3. **Draft SKILL.md** — frontmatter + instructions (see below)
4. **Add supporting files** — scripts, references, or assets if needed
5. **Validate** — run `python scripts/validate.py <skill-dir>` to check format
6. **Test** — run the skill on realistic prompts; compare against no-skill baseline
7. **Iterate** — improve based on outputs; read `references/evaluating.md`
8. **Optimize description** — tune triggering; read `references/description-optimization.md`

---

## SKILL.md Format

Every skill starts with YAML frontmatter followed by Markdown instructions.

### Frontmatter fields

| Field | Required | Notes |
|-------|----------|-------|
| `name` | Yes | Max 64 chars. Lowercase letters, numbers, hyphens only. No leading/trailing/consecutive hyphens. **Must match the directory name.** |
| `description` | Yes | Max 1024 chars. Primary trigger mechanism — describe both what the skill does AND when to use it. Include specific keywords. Be explicit about edge cases. |
| `license` | No | License name or path to bundled license file |
| `compatibility` | No | Max 500 chars. Only include if the skill has real environment requirements |
| `metadata` | No | Arbitrary key-value pairs (author, version, etc.) |
| `allowed-tools` | No | Space-delimited pre-approved tools. Experimental. |

**Minimal example:**
```yaml
---
name: roll-dice
description: Roll dice using a random number generator. Use when the user asks to roll dice, roll a die, or generate a random number from a die (d6, d20, etc.).
---
```

### Description field — the triggering mechanism

Agents only see `name` + `description` at startup. This is how they decide whether to
activate a skill. Write descriptions that:

- **Name specific contexts**: "Use when the user mentions a .pdf file, asks to fill a form, or needs to merge documents"
- **Err toward being explicit**: list adjacent use cases even if not asked — "even if they don't explicitly say 'PDF'"
- **Cover both intent and artifact**: user intent ("analyze my sales data") AND the artifact ("a CSV or Excel file")
- **Stay under 1024 characters** — descriptions grow during optimization; check the limit

---

## Writing Effective Instructions

### Add what the agent lacks, omit what it knows

Include: project-specific conventions, domain-specific procedures, non-obvious edge cases,
the specific tools or APIs to use.

Omit: general programming concepts, what the file format is, how the library works at a basic level.

### Progressive disclosure

Keep `SKILL.md` under 500 lines. Move detailed reference material to `references/` and tell
the agent *when* to read each file:

```markdown
If the API returns a non-200 status, read `references/error-codes.md`.
```

### Calibrate control

- **Be prescriptive** when operations are fragile or must follow an exact sequence
- **Explain the why** when giving the agent flexibility — it makes better decisions with context
- **Provide defaults, not menus** — pick a tool and mention alternatives briefly

### High-value patterns

**Gotchas section** — the highest-value content in many skills; add corrections as you discover them:
```markdown
## Gotchas
- The `users` table uses soft deletes. Always add `WHERE deleted_at IS NULL`.
- User ID is `user_id` in the DB, `uid` in auth, `accountId` in billing — same value.
```

**Output templates** — more reliable than prose descriptions:
```markdown
## Report format
Use this template exactly:
# [Title]
## Summary
## Key findings
## Recommendations
```

**Validation loop** — instruct the agent to verify its own work:
```markdown
1. Make edits
2. Run `python scripts/validate.py output/`
3. Fix any errors, then re-run until validation passes
```

**Bundled scripts** — if every test run independently writes the same helper logic,
bundle it in `scripts/` and reference it from SKILL.md.

---

## Scripts

Scripts should:
- Accept all input via flags/args (no interactive prompts)
- Include `--help` with description, flags, and examples
- Write structured output (JSON/CSV) to stdout; diagnostics to stderr
- Be idempotent — agents may retry commands
- Declare inline dependencies where possible (Python PEP 723 + `uv run`, Deno imports, etc.)

Reference scripts from SKILL.md using relative paths from the skill root:
```markdown
Run: `python scripts/process.py --input data.csv`
```

---

## Validation

Run the bundled validator to check your skill:

```bash
python scripts/validate.py path/to/your-skill/
```

This checks:
- `name` field constraints (regex, length, matches directory name)
- `description` field (present, under 1024 chars)
- `compatibility` field (under 500 chars if present)
- Directory structure conventions

---

## Going further

- **Testing and iteration**: read `references/evaluating.md`
- **Optimizing the description for better triggering**: read `references/description-optimization.md`
- **Full format spec**: https://agentskills.io/specification
- **Example skills**: https://github.com/anthropics/skills
- **Validation CLI**: `skills-ref validate ./my-skill` (from https://github.com/agentskills/agentskills/tree/main/skills-ref)
