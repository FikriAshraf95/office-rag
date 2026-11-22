# Decisions

A decision record captures **a choice between options that all work**, made by the user, with the reasons. It sits next to two other logs:

| Log | Holds | Example |
|---|---|---|
| Open item ([SPEC-00 §8](../specs/SPEC-00-overview.md#8-schedule-and-open-items)) | A **fact** we don't know yet; an experiment answers it | "Can Relate store map properties?" |
| **Decision** (this folder) | A **choice** between valid options; the user picks | "Commit the live store, or only snapshots?" |
| Deviation ([DEVIATIONS.md](../DEVIATIONS.md)) | Code that **knowingly differs** from a spec | "The spec says X; Relate can't, so we do Y" |

A decision changes the specs. A deviation leaves the spec alone and records the gap.

## How

1. Take the next free number (`DEC-<nnn>`; never reuse one). The `DEC-` prefix keeps decisions apart from deviations (`D<nnn>`), which the parser matches.
2. Create `DEC-<nnn>-<kebab-title>.md` from the template, with status **Proposed**, and add a row to the index.
3. Where a spec depends on the open question, add a one-line pointer to the decision.
4. **To decide:** fill in *Decision*, set the status to **Accepted (option X, date)**, apply the *If accepted* changes to the specs and milestones **in the same change**, and remove the pointers. **Rejected** and **Superseded by DEC-nnn** are the other end states.

The tool does not parse this folder yet. If decisions become part of the workflow, SPEC-02 and SPEC-03 need a `Decision` label and parsing rules first.

## Template

```markdown
# DEC-<nnn> — <title>

- **Date raised:** 2026-11-?? · **Needed by:** M0? · **Status:** Proposed
- **Specs affected:** [SPEC-0? §?](../specs/SPEC-0?-….md#…)

## Context
What the problem is and why it needs a choice now.

## Options
### A. <name>
What it means in practice. **For:** … **Against:** …

## Recommendation
Which option and why.

## If accepted
The exact spec and milestone changes each option needs.

## Decision
*(empty until the user decides)*
```

## Milestone IDs in DEC-001 to DEC-004

These records were written before the milestones were split into sub-milestones (2026-11-21), so they name the old tasks. Where they went:

| Old | New |
|---|---|
| M00.1 | M00a.1 |
| M01 (deviation parser) | M01a.5 |
| M03 (claims, `log_deviation`, `what_changed`), M03.1, M03.4, M03.10 | M03a.1, M03a.2, M03a.3, M03a.6 |
| M04.11 | M04b.7 |
| M06.1, M06.8 | M06a.1–M06a.2, M06a.4 |

## Index

| # | Title | Needed by | Status |
|---|---|---|---|
| [DEC-004](DEC-004-sample-fallback.md) | What the sample is if private-repo-app can't be published | M06 | Accepted: invented sample (O1 closed: no) |
| [DEC-003](DEC-003-claim-liveness.md) | When a claim goes stale, and what "last session" means | M03 | Accepted: 2 h TTL + forced release; since last `what_changed` |
| [DEC-002](DEC-002-graph-only-links.md) | Write deviation→task and *affects* links to Markdown, or keep them graph-only | M01 | Accepted: A, in the deviation file |
| [DEC-001](DEC-001-committed-store.md) | Commit the live store, or only snapshots | M00.1 | Accepted: snapshots; sample store as a build output |
