---
name: jira-cli
description: Shared Jira CLI utility used by other Jira skills. Provides a unified interface for interacting with the Jira REST API — fetching tickets, and extensible for comments, transitions, and more. Not invoked directly by users.
compatibility: Requires Python 3.8+, git, and network access to your Jira instance.
---

# Jira CLI

Shared utility script used as a dependency by other Jira skills. Not invoked directly by users.

## Configuration

**`.claude/settings.json`** — commit this with your project:
```json
{
  "env": {
    "JIRA_BASE_URL": "https://yourcompany.atlassian.net"
  }
}
```

**`.claude/settings.local.json`** — never commit this (add to `.gitignore`):
```json
{
  "env": {
    "JIRA_EMAIL": "you@yourcompany.com",
    "JIRA_API_TOKEN": "your-api-token"
  }
}
```

Generate an API token at: https://id.atlassian.com/manage-profile/security/api-tokens

## Commands

### `fetch <ticket>`

Fetches a ticket and saves raw JSON to `.claude/jira-tickets/<TICKET_KEY>/raw.json`. Prints a summary to stdout.

```bash
python3 ../jira-cli/scripts/jira.py fetch PROJ-123
python3 ../jira-cli/scripts/jira.py fetch 123    # infers project key from current git branch
```

The ticket number-only form extracts the project key from the current branch name. For example, on branch `feature/PROJ-123-my-feature`, `123` resolves to `PROJ-123`.
