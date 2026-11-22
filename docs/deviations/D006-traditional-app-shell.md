# D006 — Traditional app shell instead of the floating page sheet

- **Date / milestone:** 2026-11-21 · M05
- **Spec:** [SPEC-07 §3](../specs/SPEC-07-frontend.md#3-reuse-map-copy-dont-reinvent) (Layout row), [design-system §10](../design-system.md#10-components-target-look) (Navigation row)
- **Status:** Resolved → spec updated (2026-11-21)

## Spec says
- Layout: copy `AppLayout.vue`, `AppTopBar.vue` from Office Suite, change only the nav and top bar contents.
- Navigation: sidebar on `surface-page` with no edge; the current entry is a raised `surface` pill with `shadow-sm`; the top bar and page sit in a rounded `radius-xl` sheet with `shadow-sm`.

## Implementation does
- Three flush regions: a full-height sidebar on `surface` with a right border; a full-width 56px header on `surface` with a bottom border (the logo row lines up with it); content on `surface-page`.
- The current nav entry is `surface-selected` with `brand-ink` text and a 2px `brand` bar on the left (no raised pill).
- No rounded sheet, no outer padding or ring. Phones keep the drawer. The chat composer's sticky bar uses `surface-page` to match the content canvas.
- Tokens only; no new tokens.

## Why
- Product request (2026-11-21): a more traditional sidebar / header / content look.

## Consequences
- Cards, tables and panels (`surface` with a border) now stand out against the `surface-page` content area.
- Folded into design-system §10 (Navigation row) and SPEC-07 §3 (Layout row); the shell is now the spec.
