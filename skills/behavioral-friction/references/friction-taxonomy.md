# Behavioral Friction Taxonomy

These are the 8 categories of behavioral friction between a model and its user.
Every category describes a failure in the interaction dynamic, not a technical
bug. The distinction matters: "model used wrong API" is technical; "model
started coding before user finished explaining" is behavioral.

When classifying an incident, pick the single best-fit category. If two apply,
pick the one where the user's correction signal was strongest.

---

## 1. premature_execution

The model acts before the user has finished thinking, explaining, or giving
explicit go-ahead. The user was still deliberating, sharing context, or
exploring options, and the model jumped to implementation.

Signals:
- User was mid-thought or mid-plan and model started writing code/files
- User said something like "let me think", "hold on", "before we do that"
- User had to say "stop", "wait", "I wasn't done"
- Model produced output the user immediately discarded or reverted

NOT this category if the user gave a clear instruction and the model just
executed it poorly (that's a technical/implementation issue, out of scope).

---

## 2. intent_misread

The model interpreted the user's request differently than what was meant. The
user asked for X and the model delivered Y, not because of a technical failure
but because of a misunderstanding of what X was.

Signals:
- User said "that's not what I meant"
- User restated the same request with different words
- Model's response addressed a different problem than the one described
- User had to explain the same concept multiple times

NOT this category if the model understood the intent but chose a bad
implementation (that's a technical/implementation issue, or scope_creep).

---

## 3. scope_creep

The model expanded the scope of work beyond what the user asked for.
Refactored files that weren't mentioned. Added features that weren't
requested. Changed things that were working fine. Reorganized code structure
when asked to fix a bug.

Signals:
- User said "I only asked you to..."
- User said "why did you change X, I didn't ask for that"
- User had to revert unrelated changes
- Model touched files or systems outside the stated task boundary

---

## 4. ignored_preference

The user has a stated or previously-communicated preference and the model
violated it. This includes explicit CLAUDE.md rules, corrections given earlier
in the same session, and patterns the user has reinforced repeatedly.

Signals:
- User said "I already told you to..."
- User repeated an instruction they gave earlier in the session
- Model used a pattern/style/approach the user previously rejected
- The behavior contradicts a rule in CLAUDE.md or a prior correction

---

## 5. assumed_context

The model made an assumption about the user's environment, intent, or
knowledge that wasn't stated and turned out to be wrong. The model filled in
blanks instead of asking.

Signals:
- Model assumed a tech stack, framework, or tool the user doesn't use
- Model assumed the user's level of expertise (too basic or too advanced)
- Model assumed what "done" means without checking
- User said "I'm not using X" or "that's not how my project works"

NOT this category for reasonable defaults that turned out wrong, nor for the
model picking a wrong tool/framework when the user had specified the stack or
gave a clear instruction (that is a technical choice, out of scope). Only
classify here when the model filled an UNSTATED blank that asking would have
resolved.

---

## 6. over_explanation

The model produced verbose explanations, caveats, or pedagogical content when
the user wanted concise action. The user's communication style signals
expertise and brevity, but the model defaulted to tutorial mode.

Signals:
- User said "just do it", "skip the explanation", "I know"
- User's own messages are terse and the model's responses are walls of text
- User repeatedly ignores or doesn't acknowledge explanatory paragraphs
- Model restated what the user already said back to them before acting

---

## 7. confirmation_failure

The model should have confirmed before acting (destructive action,
irreversible change, ambiguous instruction) but didn't. Or the reverse: the
model asked for confirmation on something trivially safe, creating unnecessary
friction and slowing the user down.

Signals (should have confirmed):
- User had to undo a destructive action
- Model deleted, overwrote, or restructured without checking
- User said "you should have asked first"

Signals (shouldn't have asked):
- User expressed frustration at being asked obvious questions
- User said "just do it" or "stop asking"
- The action was clearly within the scope of what was requested

---

## 8. correction_resistance

The user gave a correction and the model didn't fully absorb it. The model
either argued back, partially applied the correction, or reverted to the
previous behavior within the same session.

Signals:
- User gave the same correction more than once in a session
- Model acknowledged the correction but continued the old behavior
- Model pushed back on a preference that isn't up for debate
- User escalated tone after a correction wasn't absorbed

---

## Exclusions

Do NOT classify these as behavioral friction:

- Model produced buggy code (technical)
- Model used the wrong library or API (technical)
- Model hit a tool error or permission issue (environmental)
- Model ran out of context or compacted at a bad time (architectural)
- User changed their mind mid-task (user-initiated, not friction)
- Disagreement where the user asked for the model's opinion and got one
  (working as intended)
