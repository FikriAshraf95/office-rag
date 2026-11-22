# Deviations

A deviation is any place where the code knowingly differs from a spec. **An unlogged deviation is a bug.**

## When to log
- A spec instruction is impossible or wrong in practice.
- Two spec sections contradict each other.
- A materially different approach: library, table shape, endpoint contract, event shape.
- A spec item deliberately skipped.

## When not to log
- Naming or formatting the specs don't dictate.
- Bug fixes that move code closer to the spec.

More than a couple of deviations in one milestone means the *Read first* list needs re-reading.

## How
1. Before writing, check the **highest D-number** in the index below; take the next one (never reuse a number).
2. Create `deviations/D<nnn>-<kebab-title>.md` from the template, **in the same change as the code**.
3. Add a row at the **top** of the index.
4. At the spec section, add: `> **DEVIATION:** see [D<nnn>](../deviations/D<nnn>-….md) — one-line summary`.
5. If it should become the rule: update the spec instead, set the deviation's status to **Resolved → spec updated**, and remove the note from the spec.

Open deviations are folded into the specs at M99 (and whenever one spec collects several).

## Template

```markdown
# D<nnn> — <title>

- **Date / milestone:** 2026-11-?? · M0?
- **Spec:** [SPEC-0? §?](../specs/SPEC-0?-….md#…)
- **Status:** Open | Resolved → spec updated

## Spec says
…

## Implementation does
…

## Why
…

## Consequences
…
```

## Index (newest first)

| # | Title | Milestone | Spec | Status |
|---|---|---|---|---|
| [D009](deviations/D009-vision-instruction-line-format.md) | Vision instruction fixes the org-chart line format and asks for free-standing labels | M07 | SPEC-03 §8 | Resolved → spec updated |
| [D008](deviations/D008-vision-and-summary-details.md) | Vision fallback covers standalone images only; summary and tags are best-effort | M07 | SPEC-03 §8 | Resolved → spec updated |
| [D007](deviations/D007-eval-http-client-in-providers.md) | The eval script gets its HTTP client from `providers/api_client.py` | M06 | SPEC-01 §2 | Resolved → spec updated |
| [D006](deviations/D006-traditional-app-shell.md) | Traditional sidebar / header / content shell instead of the floating page sheet | M05 | SPEC-07 §3; design-system §10 | Resolved → spec updated |
| [D005](deviations/D005-answering-implementation-details.md) | Answering differs from SPEC-05/SPEC-01 in three details (history query fit, null `done.model`, `detect_language` import) | M04 | SPEC-05 §1, §6; SPEC-01 §2 | Resolved → spec updated |
| [D004](deviations/D004-malay-language-line-in-prompt.md) | Malay language line in the prompt (prompt v2) | M04 | SPEC-05 §2 | Resolved → spec updated |
| [D003](deviations/D003-code-token-needs-letter-and-digit.md) | Gate code token needs a letter and a digit, not just a digit | M03 | SPEC-04 §4 | Resolved → spec updated |
| [D002](deviations/D002-ingestion-parsing-and-chunking-details.md) | Ingestion parsing and chunking differ from SPEC-03 in six details | M02 | SPEC-03 §4, §5.1, §5.2, §6 | Resolved → spec updated |
| [D001](deviations/D001-answer-sanitizer-and-safehtml.md) | Answer sanitizer and SafeHtml differ from the kit copy | M00 | SPEC-07 §3 | Resolved → spec updated |
