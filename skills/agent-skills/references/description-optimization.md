# Optimizing Skill Descriptions

Read this when the skill is working but not triggering reliably on the prompts it should.

## How triggering works

At startup, agents see only `name` + `description` for each skill. When a user's request matches a description, the agent loads the full `SKILL.md` and follows its instructions.

Agents typically only reach for skills when the task needs specialized knowledge — a simple one-step request may not trigger even with a perfect description. Complex, multi-step, or domain-specific requests are where descriptions make the difference.

## Principles for effective descriptions

- **Imperative phrasing**: "Use this skill when..." not "This skill does..."
- **User intent, not implementation**: what the user is trying to achieve, not how the skill works internally
- **Be explicit**: list contexts where the skill applies, including when the user doesn't name the domain — "even if they don't say 'CSV' or 'analysis'"
- **Stay under 1024 characters**: descriptions grow during optimization; check frequently

## Testing trigger accuracy

Create ~20 eval queries: 8–10 that should trigger, 8–10 that shouldn't.

```json
[
  { "query": "...", "should_trigger": true },
  { "query": "...", "should_trigger": false }
]
```

### Should-trigger queries

Vary along:
- **Phrasing**: formal, casual, typos, abbreviations
- **Explicitness**: some name the domain directly ("analyze this CSV"), others don't ("my boss wants a chart from this data file")
- **Length**: short one-liners and context-heavy messages with file paths/column names/backstory
- **Complexity**: single-step tasks AND multi-step workflows

The most valuable should-trigger cases are those where the connection isn't obvious from the query — description wording makes the difference.

### Should-not-trigger queries (near-misses are most valuable)

Weak negatives: "Write a fibonacci function" — too obviously irrelevant.

Strong negatives share keywords but need something different:
- For a CSV analysis skill: "write a Python script that reads a CSV and uploads rows to Postgres" — involves CSV but the task is ETL, not analysis
- For a PDF skill: "generate a PDF from this HTML using headless Chrome" — involves PDF but needs a web automation skill

### Running the test

For each query:
1. Run it through your agent with the skill installed
2. Check execution logs to see whether the skill was consulted
3. Run 3 times per query to account for model nondeterminism
4. Compute trigger rate (fraction of runs where skill activated)

A should-trigger query passes if trigger rate > 0.5.
A should-not-trigger query passes if trigger rate < 0.5.

## The optimization loop

1. Split queries: **60% train**, **40% validation** (hold the validation set out entirely)
2. Evaluate current description on train set — identify failing queries
3. Revise description based on train failures only
   - Should-trigger failing → description is too narrow; broaden scope, add context
   - Should-not-trigger false-firing → too broad; add specificity about what the skill doesn't do
   - Avoid adding specific keywords from failed queries — generalize the category instead
4. Re-evaluate on train set; repeat up to 5 iterations
5. Select the best iteration by **validation** pass rate (not train rate, to avoid overfitting)

## Applying the result

```yaml
# Before
description: Process CSV files.

# After
description: >
  Analyze CSV and tabular data files — compute summary statistics,
  add derived columns, generate charts, and clean messy data. Use this
  skill when the user has a CSV, TSV, or Excel file and wants to
  explore, transform, or visualize the data, even if they don't
  explicitly mention "CSV" or "analysis."
```

After updating: verify under 1024 chars, then manually spot-check 3–5 prompts.
