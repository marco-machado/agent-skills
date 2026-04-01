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

Fetch a Jira ticket and produce a structured analysis document.

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

## Configuration

The following environment variables are required:

| Variable | Description |
|---|---|
| `JIRA_BASE_URL` | Your Jira instance URL (e.g. `https://yourcompany.atlassian.net`) |
| `JIRA_EMAIL` | Your Jira account email |
| `JIRA_API_TOKEN` | Your Jira API token |

Generate an API token at https://id.atlassian.com/manage-profile/security/api-tokens.

The script checks `os.environ` first, so any of the following approaches work:

**`.env` files** (recommended for projects) — the script automatically loads these from the project root:
```
# .env — commit this
JIRA_BASE_URL=https://yourcompany.atlassian.net

# .env.local — add to .gitignore, never commit
JIRA_EMAIL=you@yourcompany.com
JIRA_API_TOKEN=your-api-token
```

**Agent config** — set via your agent's native environment mechanism, e.g. Claude Code's `.claude/settings.json` (`env` section) and `.claude/settings.local.json` for secrets.

**Shell environment** — export directly before running:
```bash
export JIRA_BASE_URL=https://yourcompany.atlassian.net
export JIRA_EMAIL=you@yourcompany.com
export JIRA_API_TOKEN=your-api-token
```

## Usage

Skills are automatically available once installed. The agent will use them when relevant tasks are detected.

**Examples:**
```
Start ticket PROJ-189
```
```
Fetch ticket 189
```

## Skill Structure

Skills live under `skills/` and each contains:
- `SKILL.md` - Instructions for the agent
- `scripts/` - Helper scripts for automation (optional)
- `references/` - Supporting documentation (optional)

## License

MIT
