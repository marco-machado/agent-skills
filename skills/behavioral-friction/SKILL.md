---
name: behavioral-friction
description: >
  Analyze Claude Code session transcripts to extract behavioral friction between
  the model and the user. Focuses exclusively on interaction dynamics, not
  technical failures. Identifies patterns like intent misreads, unasked-for
  actions, assumption leaps, scope creep, ignored preferences, premature
  execution, and repeated corrections. Outputs durable CLAUDE.md rules derived
  from real evidence. Use this skill when the user says things like "analyze my
  transcripts", "extract rules from my sessions", "what friction patterns do I
  have with Claude", "generate CLAUDE.md rules from my history", "review my
  session friction", or "what does Claude keep getting wrong about me". Also
  trigger when the user wants to improve their CLAUDE.md based on actual session
  behavior rather than guesswork.
user-invocable: true
allowed-tools: Bash, Read, Glob, Write, Task
compatibility: >
  Claude Code only. Reads local session transcripts under ~/.claude/projects and
  dispatches Task subagents for extraction. Requires Python 3.8+ for the corpus
  preprocessor.
metadata:
  version: "1.0.0"
  author: marco-machado
---

# Behavioral Friction Extractor

Extract durable interaction rules from Claude Code transcripts by analyzing
behavioral friction between the model and the user. This skill ignores
technical failures (wrong API, buggy code, tool errors, dependency issues) and
focuses entirely on the human-model dynamic: where did the model misread what
the user wanted, act without permission, assume something unstated, or repeat
a mistake the user had already corrected?

## What this skill is NOT

This is not /insights. /insights reports on tool usage stats, session
durations, and general friction categories that blend technical and behavioral
issues. This skill does the opposite: it reads raw transcripts, filters for
interaction-pattern evidence only, and produces rules that change how the model
behaves with this specific user.

## Privacy and consent

Transcripts can contain secrets the user pasted (keys, tokens, .env values) and
private content. Before the first run, tell the user plainly: "This reads your
local session transcripts under ~/.claude/projects, analyzes them on this
machine, and writes a report here. Nothing is uploaded beyond the normal model
calls. Proceed?"

All processing is local. The preprocessor redacts common secret patterns before
any transcript text reaches a subagent, so quoted evidence in the final report
is already scrubbed. Do not defeat this by quoting raw transcript lines from
elsewhere.

## Corpus

Claude Code stores session transcripts as JSONL files under
`~/.claude/projects/<project-hash>/<session-id>.jsonl`. Subagent transcripts
live under a `subagents/` subdirectory and are excluded.

Do not parse these files by hand. The record schema is non-obvious (top-level
`type` is `user`/`assistant`; tool calls appear as `tool_use` blocks nested in
`message.content`, and also as separate top-level records). The preprocessor in
`scripts/prepare_corpus.py` handles all of this, plus subagent filtering,
mtime sorting, payload stripping, redaction, and session tagging.

## Pipeline

```
1. PREPARE    python scripts/prepare_corpus.py  -> manifest.json + per-session digests
2. EXTRACT    one Task subagent per digest, using references/extraction-prompt.md
3. AGGREGATE  merge incidents (stamped with session_id/date), dedupe, drop vague signals
4. SYNTHESIZE references/synthesis-prompt.md over incidents + corpus metadata
5. OUTPUT     write behavioral-friction-report.md, offer to update CLAUDE.md
```

## Step 1: PREPARE

Run the preprocessor (it makes no model calls):

```bash
python3 scripts/prepare_corpus.py            # last 30 sessions, all projects
python3 scripts/prepare_corpus.py --dry-run  # corpus stats only, writes nothing
python3 scripts/prepare_corpus.py --period 2026-05 2026-06
python3 scripts/prepare_corpus.py --project my-app
python3 scripts/prepare_corpus.py --limit 50
```

If the user passed `--dry-run`, run with `--dry-run`, report the corpus stats
(total JSONL, subagent logs excluded, main sessions, selected, date range), and
stop.

Otherwise run it and read the resulting `manifest.json` (default
`./.behavioral-friction/manifest.json`). Report to the user: "Found N main
sessions (M subagent logs excluded). Analyzing K." The manifest's `corpus`
block carries the counts the synthesis step needs; the `sessions` array lists
each selected session's `session_id`, `session_date`, and `digest_path`.

## Step 2: EXTRACT (parallel)

For each session in the manifest, dispatch a Task subagent.

- System prompt: the contents of `references/extraction-prompt.md`, with
  `references/friction-taxonomy.md` appended so the subagent has the full
  category definitions.
- Input: the digest text at that session's `digest_path`.
- Model: default Sonnet. For a cheaper run the user may opt into Haiku; it works
  but raises false positives on the behavioral-vs-technical filter and on
  returning `[]` for clean sessions, so keep Sonnet as the default.

Run up to 10 Tasks in parallel to keep wall-clock time reasonable.

Each Task returns a JSON array of incidents (or `[]`). The subagent does NOT add
session metadata. After a Task returns, **stamp every incident** in its array
with the `session_id` and `session_date` from that session's manifest entry.
This is what makes distinct-session counting possible downstream.

An empty array is expected and normal. Most sessions are clean. Do not prompt
subagents to manufacture incidents.

## Step 3: AGGREGATE

Merge all stamped incident arrays into one list.

- Drop any incident whose `correction_signal` is empty or vague. The correction
  signal is the strongest evidence that real friction occurred; without it the
  user may not have cared.
- Group by `category`. For each category, count both total incidents and
  **distinct `session_id`s** (the latter drives confidence).
- Compute the clean-session count: `corpus.selected` from the manifest minus the
  number of distinct sessions that produced at least one kept incident.

## Step 4: SYNTHESIZE

Feed the synthesis step (using `references/synthesis-prompt.md`) two things:

1. the aggregated, stamped incidents, and
2. corpus metadata: sessions analyzed (`corpus.selected`), the date range, and
   the clean-session count computed in Step 3.

Confidence is measured in distinct sessions, not raw incident count, so a single
noisy session cannot inflate a pattern to HIGH.

The synthesis produces a ranked list of patterns (5 max), each with examples and
one durable, imperative, behavioral CLAUDE.md rule.

## Step 5: OUTPUT

Write the report to the current working directory as
`behavioral-friction-report.md`:

```markdown
# Behavioral Friction Report
Generated: YYYY-MM-DD
Sessions analyzed: N
Date range: YYYY-MM-DD to YYYY-MM-DD

## Summary
[1-2 sentences: the dominant pattern and overall interaction health]

## Top Friction Patterns

### 1. [Category] (M sessions, K incidents, CONFIDENCE)
[Plain-language description]

**Evidence:**
- [date]: User said "..." / Model did "..." / User corrected "..."

**Proposed CLAUDE.md rule:**
> [Imperative rule text]

## Proposed CLAUDE.md Block
[All rules in one copy-pasteable block]

## Sessions With No Friction
[Clean-session count and a note that clean sessions are a healthy signal]
```

Every "Proposed CLAUDE.md rule" must be the literal text to paste under a
CLAUDE.md bullet -- ready to insert as a new rule or to replace an existing one
wholesale. Never put commentary there ("you already have this", "the gap is
adherence", "if anything, tighten X to Y"); write the final rule itself. The
"Proposed CLAUDE.md Block" is those rule texts concatenated, paste-ready as-is.

Present the report. Ask: "Want me to append these rules to your CLAUDE.md, or
review and pick?" Do not edit CLAUDE.md without an explicit yes.

## Invocation

```
/behavioral-friction                     # last 30 days, all projects
/behavioral-friction --period 2026-05 2026-06
/behavioral-friction --project my-app
/behavioral-friction --dry-run           # corpus stats only
```

## Cost and runtime

~$2-4 per run depending on session count; 5-8 minutes for 30 sessions with
parallel extraction. PREPARE uses no model (deterministic Python). EXTRACT uses
Sonnet by default (Haiku is a cheaper toggle, see Step 2). SYNTHESIZE uses the
active model.
