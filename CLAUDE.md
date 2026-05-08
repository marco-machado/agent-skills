# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A collection of agent skills following the [agentskills open format](https://agentskills.io/). Each skill is a self-contained directory under `skills/` that packages instructions, scripts, and references for an AI agent.

## Validate a skill

```bash
python skills/agent-skills/scripts/validate.py skills/<skill-name>/
```

Exit codes: `0` = valid, `1` = validation errors, `2` = usage error. The validator checks frontmatter constraints — run it after any SKILL.md change.

## SKILL.md frontmatter constraints

| Field | Rule |
|---|---|
| `name` | Lowercase letters, numbers, hyphens only. No leading/trailing/consecutive hyphens. Max 64 chars. **Must match the directory name.** |
| `description` | Required. Max 1024 chars. This is the agent's only trigger signal — write it to cover intent and artifact. |
| `compatibility` | Optional. Max 500 chars. Only include for real environment requirements. |
| `metadata` | Optional key-value pairs. Use `version` and `author` here. |

## Architecture

```
skills/
  <skill-name>/
    SKILL.md          # frontmatter + agent instructions (keep under 500 lines)
    scripts/          # helper scripts; reference with relative paths from skill root
    references/       # detail docs loaded on demand; tell agent when to read each
    evals/
      evals.json      # test cases: prompt + expected_output + assertions
```

## Versioning

- `package.json` at repo root: bump on any skill release
- `metadata.version` in each `SKILL.md`: bump only when that skill changes
- Tag releases with `git tag v<version>`

## Git workflow

- Branching: GitHub Flow
- Commits: Conventional Commits — use the skill name as scope when a commit is scoped to one skill
- Release: tag `main` with `v<version>` (see Versioning above)

## Adding a new skill

Before creating or scaffolding a new skill, read `skills/agent-skills/SKILL.md` — it's the canonical format spec and authoring workflow. Follow it for authoring, then complete these repo-specific follow-ups:

- Add an entry to the `agent-skills` skill's `evals/evals.json` if evaluating
- Update `README.md` with the new skill entry
- Bump `package.json` version and add `metadata.version` to the new SKILL.md
