---
name: codebase-mapper
description: >
  Map a codebase by sequentially analyzing four focus areas (tech, arch,
  quality, concerns) and writing structured analysis documents to
  docs/generated/. Use when the user asks to map, document, or analyze a
  codebase, or runs /codebase-mapper. Produces STACK.md, INTEGRATIONS.md,
  ARCHITECTURE.md, STRUCTURE.md, CONVENTIONS.md, TESTING.md, CONCERNS.md.
  Includes a Refresh/Update/Abort gate when docs already exist and a
  secrets-leak scan over the generated files. Cross-client: works in any
  agentskills.io-compliant host (Claude Code, Cursor, Codex, OpenCode,
  GitHub Copilot, Gemini CLI, and more).
metadata:
  version: 1.0.0
  author: Marco Machado <marco.machado@gmail.com>
---

# codebase-mapper

Sequentially analyze a codebase across four focus areas and emit a complete
set of mapping documents to `docs/generated/`. Runs in one context — no
subagent spawning, no host-specific extensions.

## When to use

- User runs `/codebase-mapper`.
- User asks to "map", "document", "audit", or "analyze" a codebase and
  wants a structured set of mapping documents as output.

## How this works

The skill runs four focus phases **sequentially in this same context**:

| Focus      | Documents written                  |
|------------|------------------------------------|
| `tech`     | `STACK.md`, `INTEGRATIONS.md`      |
| `arch`     | `ARCHITECTURE.md`, `STRUCTURE.md`  |
| `quality`  | `CONVENTIONS.md`, `TESTING.md`     |
| `concerns` | `CONCERNS.md`                      |

Each phase has its own reference file under `references/focus-<name>.md`
containing exploration commands and document templates. The skill reads
each phase's reference file on demand, executes its commands, and writes
the corresponding document(s).

## Guiding principles (apply to every phase)

1. **File paths are critical.** Every finding needs a file path in
   backticks: `src/services/user.ts`, not "the user service".
2. **Patterns matter more than lists.** Show *how* things are done with
   code excerpts, not just *what* exists.
3. **Be prescriptive.** "Use camelCase for functions" is more useful
   than "Some functions use camelCase."
4. **`CONCERNS.md` drives priorities.** Be specific about impact and fix
   approach — these often become future work.
5. **`STRUCTURE.md` answers "where do I put this?"** Include guidance
   for adding new code, not just describing what exists.

### Document quality

- Include enough detail to be useful as reference. A 200-line `TESTING.md`
  with real patterns is more valuable than a 74-line summary.
- Write **current state only** — describe what *is*, never what *was*
  or what you considered. No temporal language.
- Be prescriptive, not descriptive — "Use X pattern" beats "X pattern is
  used."

## Workflow

### Step 1 — Inspect `docs/generated/`

Check whether `docs/generated/` exists under the current working
directory.

- **Does not exist**: create it (`mkdir -p docs/generated`) and proceed
  to Step 2 with all four focus areas selected.
- **Exists**: list its contents (`ls -1 docs/generated/`) and show the
  user. Then ask the user to choose one of:
  1. **Refresh** — delete existing `docs/generated/*.md`
     (`rm docs/generated/*.md`) and remap from scratch (all four focus
     areas).
  2. **Update** — keep existing files; ask a follow-up multiple-choice
     question listing the four focus areas; only the chosen areas re-run.
  3. **Abort** — stop the skill, return without doing anything else.

### Step 2 — Load shared guardrails

Read `references/forbidden-files.md` once. It lists files the skill
must never read or quote (`.env*`, key files, credentials). Apply
those rules in every focus phase that follows.

### Step 3 — Run focus phases (sequential)

For each selected focus area, in this fixed order — `tech`, `arch`,
`quality`, `concerns`:

1. Read `references/focus-<focus>.md`.
2. Run the exploration commands listed in that file. Read the source
   files identified during exploration.
3. Use what you learn to fill in the document templates from that file.
4. Write the document(s) directly to `docs/generated/` using the
   `Write` tool. Replace `[YYYY-MM-DD]` with today's date from session
   context. Never guess the date.

Phases run **sequentially** to bound context growth and stay portable
across hosts that don't support subagent spawning. Within a single
phase you may issue parallel tool calls (e.g. multiple `Read`s) if the
host supports them — just don't try to fan out across phases.

### Step 4 — Verify outputs

For each focus that ran, confirm its expected files exist and are
non-empty:

```bash
for f in docs/generated/<expected>.md; do
  [ -s "$f" ] || echo "MISSING_OR_EMPTY: $f"
done
```

The expected files per focus are listed in the table above. If any
expected file is missing or empty, report which focus produced the
gap and stop before the secrets scan.

### Step 5 — Secrets scan

Run the bundled scanner against the output directory:

```bash
python3 <skill_dir>/scripts/scan-secrets.py docs/generated/
```

Resolve `<skill_dir>` from this `SKILL.md`'s installed location, not
the user's cwd.

- **Exit 0**: continue silently to Step 6.
- **Exit 1** (hits found): emit this warning verbatim, then the
  scanner's stdout, then advise the user to review and redact before
  committing. **Do not auto-delete or auto-redact.**

  ```
  ⚠️  SECURITY ALERT: Potential secrets detected in codebase documents!
  ```

### Step 6 — Final summary

A short block:

- Focus areas that ran: `tech, arch, quality, concerns` (or the chosen
  subset).
- Files written: list of relative paths under `docs/generated/`.
- Secrets-scan verdict: `clean` or `N hits — review required`.

## Notes

- Sequential execution costs wall-clock vs. parallel spawning, but it
  works in every agentskills.io-compliant host (Claude Code, Cursor,
  Codex, OpenCode, GitHub Copilot, Gemini CLI, and more) — no
  host-specific extensions, no separate agent files to install.
- `<forbidden_files>` rules are non-negotiable. Note file existence
  only; never quote contents. The post-scan is a safety net.
- Re-running on a clean repo (no `docs/generated/`) and re-running with
  Refresh produce equivalent output.
