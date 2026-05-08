# Focus: concerns

## Goal

Identify technical debt, fragile areas, and gaps that risk future work.

## Documents to write

- `docs/generated/CONCERNS.md`

## Exploration commands

```bash
# TODO / FIXME / HACK / XXX comments
grep -rn "TODO\|FIXME\|HACK\|XXX" src/ \
  --include="*.ts" --include="*.tsx" 2>/dev/null | head -50

# Largest files (potential complexity hotspots)
find src/ -name "*.ts" -o -name "*.tsx" 2>/dev/null \
  | xargs wc -l 2>/dev/null | sort -rn | head -20

# Empty returns / stubs
grep -rn "return null\|return \[\]\|return {}" src/ \
  --include="*.ts" --include="*.tsx" 2>/dev/null | head -30
```

Read the largest files and the files with the most TODO/FIXME density
to ground concerns in concrete `file:line` references. Concerns without
a file path are not actionable — drop them.

## Template — `CONCERNS.md`

Replace `[YYYY-MM-DD]` with today's date. Be specific about impact and
fix approach — these entries often become future work.

```markdown
# Codebase Concerns

**Analysis Date:** [YYYY-MM-DD]

## Tech Debt

**[Area/Component]:**
- Issue: [What's the shortcut/workaround]
- Files: `[file paths]`
- Impact: [What breaks or degrades]
- Fix approach: [How to address it]

## Known Bugs

**[Bug description]:**
- Symptoms: [What happens]
- Files: `[file paths]`
- Trigger: [How to reproduce]
- Workaround: [If any]

## Security Considerations

**[Area]:**
- Risk: [What could go wrong]
- Files: `[file paths]`
- Current mitigation: [What's in place]
- Recommendations: [What should be added]

## Performance Bottlenecks

**[Slow operation]:**
- Problem: [What's slow]
- Files: `[file paths]`
- Cause: [Why it's slow]
- Improvement path: [How to speed up]

## Fragile Areas

**[Component/Module]:**
- Files: `[file paths]`
- Why fragile: [What makes it break easily]
- Safe modification: [How to change safely]
- Test coverage: [Gaps]

## Scaling Limits

**[Resource/System]:**
- Current capacity: [Numbers]
- Limit: [Where it breaks]
- Scaling path: [How to increase]

## Dependencies at Risk

**[Package]:**
- Risk: [What's wrong]
- Impact: [What breaks]
- Migration plan: [Alternative]

## Missing Critical Features

**[Feature gap]:**
- Problem: [What's missing]
- Blocks: [What can't be done]

## Test Coverage Gaps

**[Untested area]:**
- What's not tested: [Specific functionality]
- Files: `[file paths]`
- Risk: [What could break unnoticed]
- Priority: [High/Medium/Low]

---

*Concerns audit: [date]*
```
