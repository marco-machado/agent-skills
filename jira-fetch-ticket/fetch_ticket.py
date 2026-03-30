#!/usr/bin/env python3
"""
Fetch a Jira ticket and save raw JSON to docs/jira-tickets/<TICKET_KEY>/raw.json.

Usage:
  python3 fetch_ticket.py PROJ-123
  python3 fetch_ticket.py 123       # infers project key from current git branch

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
TICKETS_DIR = os.path.join("docs", "jira-tickets")


def load_dotenv_file(path):
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


def normalize_key(raw):
    raw = raw.strip().upper()
    if re.match(r"^[A-Z]+-\d+$", raw):
        return raw
    if raw.isdigit():
        result = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True)
        branch = result.stdout.strip() if result.returncode == 0 else ""
        match = re.search(r"([A-Z]+)-\d+", branch.upper())
        if match:
            return f"{match.group(1)}-{raw}"
        print(f"ERROR: Cannot infer project key from branch '{branch}'")
        print("       Provide the full ticket ID (e.g. PROJ-123).")
        sys.exit(1)
    print(f"ERROR: Invalid ticket ID: {raw!r}")
    print("       Use PROJ-123 format or just the ticket number.")
    sys.exit(1)


def jira_get(config, path, exit_on_error=True):
    base = config["JIRA_BASE_URL"].rstrip("/")
    url = f"{base}{path}"
    req = Request(url, headers={"Authorization": auth_header(config), "Accept": "application/json"})
    try:
        with urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        if not exit_on_error:
            return None
        body = e.read().decode() if e.fp else ""
        print(f"ERROR: Jira API {e.code} for {url}: {body[:500]}")
        sys.exit(1)


def fetch_dev_status(config, issue_id):
    result = {}
    for dtype in DEV_STATUS_TYPES:
        for app_type in DEV_STATUS_APP_TYPES:
            path = f"/rest/dev-status/latest/issue/detail?issueId={issue_id}&applicationType={app_type}&dataType={dtype}"
            data = jira_get(config, path, exit_on_error=False)
            if data and data.get("detail"):
                result[dtype] = data
                break
        if dtype not in result:
            result[dtype] = None
    return result


def format_parent(parent):
    if not parent:
        return "None"
    summary = parent.get("fields", {}).get("summary", "")
    return f"{parent['key']}: {summary}"


def print_summary(data):
    fields = data["fields"]
    assignee = fields.get("assignee")
    parent = fields.get("parent")

    print(f"KEY:      {data['key']}")
    print(f"SUMMARY:  {fields.get('summary')}")
    print(f"TYPE:     {fields.get('issuetype', {}).get('name')}")
    print(f"STATUS:   {fields.get('status', {}).get('name')}")
    print(f"PRIORITY: {fields.get('priority', {}).get('name')}")
    print(f"ASSIGNEE: {assignee.get('displayName') if assignee else 'Unassigned'}")
    print(f"PARENT:   {format_parent(parent)}")
    print(f"LABELS:   {fields.get('labels', [])}")
    print(f"CREATED:  {fields.get('created', '')[:10]}")
    print(f"ENV:      {fields.get('environment') or 'None'}")

    subtasks = fields.get("subtasks", [])
    print(f"SUBTASKS: {len(subtasks)}")
    for subtask in subtasks:
        sub_fields = subtask.get("fields", {})
        print(f"  - {subtask['key']}: {sub_fields.get('summary', '')} ({sub_fields.get('status', {}).get('name', '')})")

    links = fields.get("issuelinks", [])
    print(f"LINKS:    {len(links)}")
    for link in links:
        link_type = link.get("type", {}).get("name", "")
        for direction in ("outwardIssue", "inwardIssue"):
            issue = link.get(direction)
            if issue:
                label = direction.replace("Issue", "").lower()
                print(f"  - {link_type} ({label}): {issue['key']} — {issue.get('fields', {}).get('summary', '')}")

    comments = fields.get("comment", {}).get("comments", [])
    print(f"COMMENTS: {len(comments)}")
    for comment in comments:
        author = comment.get("author", {}).get("displayName", "Unknown")
        created = comment.get("created", "")[:10]
        body = comment.get("body", "")[:200]
        print(f"  - {author} ({created}): {body}")

    print("---DESCRIPTION---")
    print(fields.get("description", "(none)"))


def print_dev_status(dev_status):
    branch_data = dev_status.get("branch")
    pr_data = dev_status.get("pullrequest")

    branches = [branch.get("name", "") for detail in (branch_data or {}).get("detail", []) for branch in detail.get("branches", [])]
    print(f"BRANCHES: {len(branches)}")
    for branch_name in branches:
        print(f"  - {branch_name}")

    pull_requests = [pr for detail in (pr_data or {}).get("detail", []) for pr in detail.get("pullRequests", [])]
    print(f"PULL REQUESTS: {len(pull_requests)}")
    for pr in pull_requests:
        print(f"  - #{pr.get('id')} [{pr.get('status', '').upper()}]: {pr.get('name')}")
        source = pr.get("source", {}).get("branch", "")
        destination = pr.get("destination", {}).get("branch", "")
        if source or destination:
            print(f"    {source} → {destination}")
        if pr.get("url"):
            print(f"    {pr['url']}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 fetch_ticket.py <ticket>")
        sys.exit(1)

    key = normalize_key(sys.argv[1])
    config = load_config()

    print(f"Fetching {key}...")
    data = jira_get(config, f"/rest/api/2/issue/{key}?fields={FETCH_FIELDS}")

    dev_status = {}
    if data.get("id"):
        print(f"Fetching dev status for issue {data['id']}...")
        dev_status = fetch_dev_status(config, data["id"])

    out_dir = os.path.join(TICKETS_DIR, key)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "raw.json")
    with open(out_path, "w") as f:
        json.dump({**data, "dev_status": dev_status}, f, indent=2)
    print(f"Saved to {out_path}\n")

    print_summary(data)
    if dev_status:
        print_dev_status(dev_status)


if __name__ == "__main__":
    main()
