# Agent Skills

A collection of skills for AI coding agents. Skills are packaged instructions and scripts that extend agent capabilities.

Skills follow the [Agent Skills](https://agentskills.io/) format.

## Available Skills

### jira-fetch-ticket

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
- Produces a structured `.claude/jira-tickets/TICKET_KEY/TICKET_KEY.md` document

### jira-cli

Shared Jira CLI utility used as a dependency by other Jira skills. Provides a unified interface for interacting with the Jira REST API.

> Not invoked directly — used internally by other skills in this collection.

## Installation

```bash
npx skills add marco-machado/agent-skills
```

## Configuration

Skills in this collection require the following environment variables, split across two files in your project's `.claude/` directory:

**`.env`** — commit this with your project:
```
JIRA_BASE_URL=https://yourcompany.atlassian.net
```

**`.env.local`** — never commit this (add to `.gitignore`):
```
JIRA_EMAIL=you@yourcompany.com
JIRA_API_TOKEN=your-api-token
```

Generate an API token at https://id.atlassian.com/manage-profile/security/api-tokens.

Variables can also be set directly in the environment — the script checks `os.environ` first, then falls back to the `.env` files.

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

Each skill contains:
- `SKILL.md` - Instructions for the agent
- `scripts/` - Helper scripts for automation (optional)
- `references/` - Supporting documentation (optional)

## License

MIT
