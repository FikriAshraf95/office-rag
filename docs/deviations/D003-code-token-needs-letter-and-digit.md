# D003 — Code token needs a letter and a digit

- **Date / milestone:** 2026-11-20 · M03
- **Spec:** [SPEC-04 §4](../specs/SPEC-04-retrieval.md#4-relevance-gate)
- **Status:** Resolved → spec updated (folded at M99, 2026-11-21)

## Spec says
The relevance gate also passes when the query contains a **code token** ("a word with a digit, e.g. `M2`, `Q4`, a form number") and a candidate found by the full-text arm contains that token.

## Implementation does
A code token is a `[\w-]+` word with **at least one letter and at least one digit** (`M2`, `Q4`, `E1`, `HR-F07`). Pure numbers (`6`, `2026`, `10`) are not code tokens. The token must occur as a whole word (case-insensitive, not inside a longer word such as `M20`) in the text of a candidate whose `fts_rank` is set. Implemented in `code_tokens()` and `passes_gate()` in `backend/app/retrieval/search.py`.

## Why
Questions are full of plain numbers ("pet policy 2026", "6 years", "10 days"). Under the literal rule, any such number found in any chunk would open the gate for an unrelated question, defeating the "never guess" gate (SPEC-04 §8 check 8).

## Consequences
A query whose only distinguishing token is a bare number (for example "grade 3") is decided by vector similarity alone. Form numbers and grade codes, the intended use, still pass. Fold into SPEC-04 §4 at M99.
