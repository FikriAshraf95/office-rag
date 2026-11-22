# D001 — Answer sanitizer and SafeHtml differ from the kit copy

- **Date / milestone:** 2026-11-20 · M00
- **Spec:** [SPEC-07 §3](../specs/SPEC-07-frontend.md#3-reuse-map-copy-dont-reinvent)
- **Status:** Resolved → spec updated (folded at M99, 2026-11-21)

## Spec says
- `SafeHtml.vue`: copy from Private Repo App, change: none.
- `sanitize.ts`: answer allowlist; `button` only with `class="citation"`, `data-cite` and `aria-label`; `a` only with `href` (http/https/mailto).

## Implementation does
- `SafeHtml.vue` drops the kit's `snippet` prop and `sanitizeSnippet`, and always calls `sanitizeAnswer`.
- Links keep only an http/https/mailto `href` from the input, and the sanitizer then adds `target="_blank" rel="noopener noreferrer nofollow"` (as the kit does).
- Citation buttons also get `type="button"`. A `button` without `class="citation"`, a numeric `data-cite` and a non-empty `aria-label` is replaced by its text.

## Why
- Once `sanitize.ts` holds only the answer allowlist (which this spec section requires), the kit's rich-text and snippet allowlists that `SafeHtml.vue` called no longer exist, so "change: none" can't compile.
- `target`/`rel` on links stops a model-written link from controlling the opener page. `type="button"` stops a citation from submitting an enclosing form.

## Consequences
- Every `SafeHtml` use renders through the answer allowlist; there is no other HTML source in this app.
- The added attributes are set by the sanitizer, never taken from model output, so the allowlist for input is unchanged.
- Fold into SPEC-07 §3 at M99: "`SafeHtml.vue`: answer allowlist only; links get `target`/`rel`; citation buttons get `type="button"`".
