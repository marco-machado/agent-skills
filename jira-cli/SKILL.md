---
name: jira-cli
description: Shared Jira CLI utility used by other Jira skills. Provides a unified interface for interacting with the Jira REST API — fetching tickets, and extensible for comments, transitions, and more. Not invoked directly by users.
compatibility: Requires Python 3.8+ and network access to your Jira instance. git is optional (used to infer project key from branch name when only a ticket number is provided).
---

# Jira CLI

Shared utility script used as a dependency by other Jira skills. Not invoked directly by users.

## Configuration

**`.env`** — commit this with your project:
```
JIRA_BASE_URL=https://yourcompany.atlassian.net
```

**`.env.local`** — never commit this (add to `.gitignore`):
```
JIRA_EMAIL=you@yourcompany.com
JIRA_API_TOKEN=your-api-token
```

Generate an API token at: https://id.atlassian.com/manage-profile/security/api-tokens

Variables can also be set directly in the environment — the script checks `os.environ` first, then falls back to the `.env` files.

## Commands

### `fetch <ticket>`

Fetches a ticket and saves raw JSON to `docs/jira-tickets/<TICKET_KEY>/raw.json`. Prints a summary to stdout.

```bash
python3 ../jira-cli/scripts/jira.py fetch PROJ-123
python3 ../jira-cli/scripts/jira.py fetch 123    # infers project key from current git branch
```

The ticket number-only form extracts the project key from the current branch name. For example, on branch `feature/PROJ-123-my-feature`, `123` resolves to `PROJ-123`.
