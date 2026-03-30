#!/usr/bin/env python3
"""
Jira CLI for agent skills.

Usage:
  python3 jira.py fetch <ticket>    # PROJ-123 or just 123 (infers project from git branch)

Configuration:
  Set via environment variables, or place in .env / .env.local in the current directory:

  .env        (commit this)  -> JIRA_BASE_URL
  .env.local  (gitignore)    -> JIRA_EMAIL, JIRA_API_TOKEN
"""

import json
import os
import re
import subprocess
import sys
from base64 import b64encode
from urllib.error import HTTPError
from urllib.request import Request, urlopen

FETCH_FIELDS = "summary,description,environment,status,issuetype,priority,assignee,parent,labels,comment,issuelinks,subtasks,created,updated"
DEV_STATUS_TYPES = ["pullrequest", "branch"]
DEV_STATUS_APP_TYPES = ["stash", "bitbucket"]


def tickets_dir():
    return os.path.join(os.getcwd(), "docs", "jira-tickets")


# --- Config & Auth ---

def load_dotenv_file(path):
    """Load key=value pairs from a .env file into a dict."""
    result = {}
    if not os.path.exists(path):
        return result
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                result[k.strip()] = v.strip()
    return result


def load_config():
    cwd = os.getcwd()
    dotenv = {
        **load_dotenv_file(os.path.join(cwd, ".env")),
        **load_dotenv_file(os.path.join(cwd, ".env.local")),
    }

    sources = {
        "JIRA_BASE_URL": ".env (project config)",
        "JIRA_EMAIL": ".env.local (user credentials)",
        "JIRA_API_TOKEN": ".env.local (user credentials)",
    }
    config = {}
    missing = []
    for key, source in sources.items():
        val = os.environ.get(key) or dotenv.get(key)
        if not val:
            missing.append(f"  {key}  →  {source}")
        else:
            config[key] = val
    if missing:
        print("ERROR: Missing required environment variables:")
        for m in missing:
            print(m)
        sys.exit(1)
    return config


def auth_header(config):
    creds = b64encode(f"{config['JIRA_EMAIL']}:{config['JIRA_API_TOKEN']}".encode()).decode()
    return f"Basic {creds}"


# --- Key normalization ---

def get_branch():
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def normalize_key(raw):
    raw = raw.strip().upper()
    if re.match(r"^[A-Z]+-\d+$", raw):
        return raw
    if raw.isdigit():
        branch = get_branch()
        match = re.search(r"([A-Z]+)-\d+", branch.upper())
        if match:
            return f"{match.group(1)}-{raw}"
        print(f"ERROR: Cannot infer project key from branch '{branch}'")
        print("       Provide the full ticket ID (e.g. PROJ-123).")
        sys.exit(1)
    print(f"ERROR: Invalid ticket ID: {raw!r}")
    print("       Use PROJ-123 format or just the ticket number.")
    sys.exit(1)


# --- HTTP helpers ---

def jira_get(config, path):
    base = config["JIRA_BASE_URL"].rstrip("/")
    url = f"{base}{path}"
    req = Request(url, headers={
        "Authorization": auth_header(config),
        "Accept": "application/json",
    })
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"ERROR: Jira API {e.code} for {url}: {body[:500]}")
        sys.exit(1)


# --- Dev status ---

def fetch_dev_status(config, issue_id):
    result = {}
    for dtype in DEV_STATUS_TYPES:
        for app_type in DEV_STATUS_APP_TYPES:
            path = f"/rest/dev-status/latest/issue/detail?issueId={issue_id}&applicationType={app_type}&dataType={dtype}"
            base = config["JIRA_BASE_URL"].rstrip("/")
            req = Request(f"{base}{path}", headers={
                "Authorization": auth_header(config),
                "Accept": "application/json",
            })
            try:
                with urlopen(req) as resp:
                    data = json.loads(resp.read().decode())
                if data.get("detail"):
                    result[dtype] = data
                    break
            except HTTPError:
                pass
        if dtype not in result:
            result[dtype] = None
    return result


# --- Output printers ---

def print_summary(data):
    f = data["fields"]
    key = data["key"]
    a = f.get("assignee")
    p = f.get("parent")

    print(f"KEY:      {key}")
    print(f"SUMMARY:  {f.get('summary')}")
    print(f"TYPE:     {f.get('issuetype', {}).get('name')}")
    print(f"STATUS:   {f.get('status', {}).get('name')}")
    print(f"PRIORITY: {f.get('priority', {}).get('name')}")
    print(f"ASSIGNEE: {a.get('displayName') if a else 'Unassigned'}")
    print(f"PARENT:   {p['key'] + ': ' + p.get('fields', {}).get('summary', '') if p else 'None'}")
    print(f"LABELS:   {f.get('labels', [])}")
    print(f"CREATED:  {f.get('created', '')[:10]}")
    env = f.get("environment")
    print(f"ENV:      {env if env else 'None'}")

    subtasks = f.get("subtasks", [])
    print(f"SUBTASKS: {len(subtasks)}")
    for st in subtasks:
        sf = st.get("fields", {})
        print(f"  - {st['key']}: {sf.get('summary', '')} ({sf.get('status', {}).get('name', '')})")

    links = f.get("issuelinks", [])
    print(f"LINKS:    {len(links)}")
    for lnk in links:
        lt = lnk.get("type", {}).get("name", "")
        for direction in ("outwardIssue", "inwardIssue"):
            issue = lnk.get(direction)
            if issue:
                label = direction.replace("Issue", "").lower()
                print(f"  - {lt} ({label}): {issue['key']} — {issue.get('fields', {}).get('summary', '')}")

    comments = f.get("comment", {}).get("comments", [])
    print(f"COMMENTS: {len(comments)}")
    for c in comments:
        author = c.get("author", {}).get("displayName", "Unknown")
        created = c.get("created", "")[:10]
        body = c.get("body", "")[:200]
        print(f"  - {author} ({created}): {body}")

    print("---DESCRIPTION---")
    print(f.get("description", "(none)"))


def print_dev_status(dev_status):
    branch_data = dev_status.get("branch")
    pr_data = dev_status.get("pullrequest")

    branches = []
    if branch_data:
        for detail in branch_data.get("detail", []):
            for b in detail.get("branches", []):
                branches.append(b.get("name", ""))
    print(f"BRANCHES: {len(branches)}")
    for b in branches:
        print(f"  - {b}")

    prs = []
    if pr_data:
        for detail in pr_data.get("detail", []):
            for pr in detail.get("pullRequests", []):
                prs.append({
                    "id": pr.get("id", ""),
                    "name": pr.get("name", ""),
                    "status": pr.get("status", ""),
                    "url": pr.get("url", ""),
                    "source": pr.get("source", {}).get("branch", ""),
                    "destination": pr.get("destination", {}).get("branch", ""),
                })
    print(f"PULL REQUESTS: {len(prs)}")
    for pr in prs:
        print(f"  - #{pr['id']} [{pr['status'].upper()}]: {pr['name']}")
        if pr["source"] or pr["destination"]:
            print(f"    {pr['source']} → {pr['destination']}")
        if pr["url"]:
            print(f"    {pr['url']}")


# --- Commands ---

def cmd_fetch(args):
    if not args:
        print("Usage: jira.py fetch <ticket>")
        sys.exit(1)

    key = normalize_key(args[0])
    config = load_config()

    print(f"Fetching {key}...")
    data = jira_get(config, f"/rest/api/2/issue/{key}?fields={FETCH_FIELDS}")

    issue_id = data.get("id")
    dev_status = {}
    if issue_id:
        print(f"Fetching dev status for issue {issue_id}...")
        dev_status = fetch_dev_status(config, issue_id)

    out_dir = os.path.join(tickets_dir(), key)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "raw.json")
    with open(out_path, "w") as f:
        json.dump({**data, "dev_status": dev_status}, f, indent=2)
    print(f"Saved to {out_path}\n")

    print_summary(data)
    if dev_status:
        print_dev_status(dev_status)


# --- Entrypoint ---

COMMANDS = {
    "fetch": cmd_fetch,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: jira.py <command> [args]")
        print(f"Commands: {', '.join(COMMANDS)}")
        sys.exit(1)
    COMMANDS[sys.argv[1]](sys.argv[2:])


if __name__ == "__main__":
    main()
