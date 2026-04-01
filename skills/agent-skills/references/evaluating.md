# Evaluating Skill Output Quality

Read this file when ready to test whether the skill works well — not just "does it run" but "is it reliably better than no skill at all?"

## The core pattern

Run each test case twice: once **with the skill**, once **without** (baseline). The delta tells you what the skill is actually adding.

## Workspace layout

```
my-skill/
├── SKILL.md
└── evals/
    └── evals.json
my-skill-workspace/
└── iteration-1/
    ├── eval-descriptive-name/
    │   ├── with_skill/
    │   │   ├── outputs/       # Files produced
    │   │   ├── timing.json    # { total_tokens, duration_ms }
    │   │   └── grading.json   # Assertion results
    │   └── without_skill/
    │       ├── outputs/
    │       ├── timing.json
    │       └── grading.json
    └── benchmark.json         # Aggregated statistics
```

## evals.json format

```json
{
  "skill_name": "my-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "A realistic user prompt — include file paths, personal context, column names",
      "expected_output": "Human-readable description of what success looks like",
      "files": ["evals/files/example.csv"],
      "assertions": [
        "The output file is valid JSON",
        "The bar chart has labeled axes",
        "The report includes at least 3 recommendations"
      ]
    }
  ]
}
```

Write 2–3 test cases first. Don't over-invest before seeing first results.
Don't add assertions until after the first run — you often don't know what "good" looks like until the skill has run.

## Good test prompts

- Vary phrasing: some formal, some casual, some with typos
- Include realistic context: file paths, column names, company names, backstory
- Cover edge cases: malformed input, unusual requests, ambiguous instructions
- "analyze my sales CSV and make a chart" is too vague; "I have data/q4_sales.csv with revenue in col C and costs in col D — can you add a profit margin column?" is a real test

## Assertions

Good assertions are objectively verifiable:
- ✅ "The output includes a bar chart image file"
- ✅ "The chart shows exactly 3 months"
- ✅ "The cleaned CSV has fewer rows than the original"
- ❌ "The output is good" — too vague
- ❌ 'Uses exactly the phrase "Total Revenue: $X"' — too brittle

## grading.json format

```json
{
  "assertion_results": [
    {
      "text": "The output includes a bar chart image file",
      "passed": true,
      "evidence": "Found chart.png (45KB) in outputs directory"
    }
  ],
  "summary": { "passed": 3, "failed": 1, "total": 4, "pass_rate": 0.75 }
}
```

Evidence must be concrete — quote or reference the actual output.

## benchmark.json format

```json
{
  "run_summary": {
    "with_skill": {
      "pass_rate": { "mean": 0.83, "stddev": 0.06 },
      "time_seconds": { "mean": 45.0, "stddev": 12.0 },
      "tokens": { "mean": 3800, "stddev": 400 }
    },
    "without_skill": {
      "pass_rate": { "mean": 0.33, "stddev": 0.10 },
      "time_seconds": { "mean": 32.0, "stddev": 8.0 },
      "tokens": { "mean": 2100, "stddev": 300 }
    },
    "delta": { "pass_rate": 0.50, "time_seconds": 13.0, "tokens": 1700 }
  }
}
```

## Analyzing patterns

After aggregating:

- **Always-pass assertions**: remove them — they don't discriminate, they just inflate scores
- **Always-fail assertions**: either the assertion is broken or the task is too hard — fix before next iteration
- **Passes with skill, fails without**: this is where the skill adds value — understand *why*
- **High variance across runs**: instructions may be ambiguous; add examples or specificity

## Iterating

1. Collect signals: failed assertions + human feedback + execution transcripts
2. Propose improvements — generalize from examples, don't add narrow patches
3. Rerun into `iteration-2/` with baseline
4. Repeat until feedback is empty or no meaningful improvement

When giving an LLM the signals to improve the skill:
- Ask it to generalize (not patch specific examples)
- Keep the skill lean — remove instructions that don't pull their weight
- Explain the why rather than adding more ALWAYS/NEVER directives
- Bundle repeated helper logic into `scripts/`
