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
