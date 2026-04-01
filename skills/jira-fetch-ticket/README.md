# jira-fetch-ticket

Fetch a Jira ticket and produce a structured analysis document in `docs/jira-tickets/`.

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
