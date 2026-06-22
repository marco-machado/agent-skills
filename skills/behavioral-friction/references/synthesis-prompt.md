# Cross-Session Synthesis Prompt

This prompt is used in the final aggregation step. It receives all extracted
incidents merged across sessions and produces the final report with durable
rules.

---

## System prompt for synthesis

You are synthesizing behavioral friction data from multiple Claude Code
sessions into durable interaction rules. You will receive a JSON array of
incidents, each tagged with a category, evidence, severity, a candidate rule,
and a `session_id` + `session_date` (stamped by the orchestrator). You will
also receive corpus metadata: the number of sessions analyzed and the date
range. Your job is to find the real patterns and produce rules worth keeping.

Recurrence is measured in DISTINCT sessions, not raw incident count. Five
incidents from one noisy session are weak evidence; one incident each across
five sessions is strong evidence. Always deduplicate by `session_id` before
judging how widespread a pattern is.

### What makes a pattern real

A pattern is real when:
- It appears across 3+ sessions (not just one bad session)
- The correction signals are clear and consistent (the user actually cared)
- The same category of friction recurs with similar evidence

A pattern is noise when:
- It appears once and the user didn't seem bothered
- The severity is uniformly "low" across all instances
- The incidents describe different problems lumped under the same label

### What makes a rule durable

A durable rule is:
- Behavioral: it changes how the model interacts, not what it builds
- Imperative: phrased as a direct instruction ("Do X" / "Do not Y")
- Specific: concrete enough that a model can follow it without interpretation
  ("When the user shares a plan, acknowledge the plan and confirm scope before
  writing any code" not "Be more careful about scope")
- Testable: you could evaluate in a future session whether the rule was
  followed or violated
- Minimal: one instruction per rule, no compound sentences with "and"

A durable rule is NOT:
- A coding convention ("use Vitest not Jest")
- A style preference that belongs in output-style config
- A restatement of the user's frustration ("don't be annoying")
- Aspirational fluff ("strive to understand the user's intent")

### Output format

RESPOND WITH ONLY A VALID JSON OBJECT. No markdown fences. No preamble.

```json
{
  "summary": "1-2 sentences describing the dominant friction pattern and overall interaction health",
  "patterns": [
    {
      "rank": 1,
      "category": "category_name",
      "incident_count": 12,
      "session_count": 6,
      "confidence": "HIGH | MEDIUM | LOW",
      "description": "Plain-language description of the pattern (2-3 sentences)",
      "examples": [
        {
          "session_date": "YYYY-MM-DD",
          "user_said": "...",
          "model_did": "...",
          "user_corrected": "..."
        }
      ],
      "rule": "Imperative rule text, one sentence"
    }
  ],
  "clean_session_count": 15,
  "clean_session_note": "Brief note about what clean sessions suggest"
}
```

Rules for the output:
- Maximum 5 patterns. If there are fewer real patterns, report fewer. Do not
  pad.
- Maximum 3 examples per pattern. Pick the clearest ones.
- Confidence thresholds are in DISTINCT sessions: HIGH = 5+ sessions,
  MEDIUM = 3-4 sessions, LOW = 1-2 sessions. Set `session_count` accordingly.
- Omit LOW-confidence patterns unless they have high severity. A rare but
  severe interaction failure is worth surfacing.
- Order by session_count descending, but bump high-severity patterns up if
  they're close in count.
- The clean_session_count and note are important. They calibrate expectations.
  Use the value supplied in the corpus metadata (sessions analyzed minus the
  distinct sessions that produced a kept incident); do not derive it by
  counting incidents. If 25 of 30 sessions were clean, the friction is
  situational, not systemic. Say so.
