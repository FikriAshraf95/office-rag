# SPEC-07 — Frontend

> **Status:** v1 (2026-11-19) · **Owner of:** pages, components, states, the reuse map from Office Suite
> Look: [design-system.md](../design-system.md) · Endpoints: [SPEC-08](SPEC-08-api-contract.md) · Events: [SPEC-05 §6](SPEC-05-answering.md)

## 1. Stack

**Decision (2026-11-19, replaces PrimeVue from the handoff):** the frontend reuses the **Office Suite v2 UI kit** (`D:\fikri\onedrive\demo\office-suite-v2-feature-uiux-revamp\frontend`): Vue 3 + Vite + strict TypeScript, Pinia, Vue Router, **Tailwind v4 + shadcn-vue (reka-ui)**, lucide icons, `vue-sonner` toasts, design tokens generated from `docs/design-system.md`. Reason: the kit already implements the design system; copying it is faster and keeps one look across the team's apps.

Added for RAG: `markdown-it` (answers), `dompurify` (already in the kit), `pdfjs-dist` (citation viewer), `openapi-typescript` (generated API types). Node ≥ 22.

Not copied: SignalR, tiptap, FullCalendar, chart.js, adaptive cards, boards, auth store, XSRF/session handling.

## 2. Folder structure

```
frontend/src/
  app/            main.ts, App.vue, router.ts, layouts/AppLayout.vue, layouts/AppTopBar.vue, navigation.ts
  api/            http.ts (axios wrapper), sse.ts (POST + stream reader), schema.d.ts (generated)
  stores/         user.ts (chosen demo user, persisted; the config from GET /config)
  features/config/api.ts  GET /config and /me
  components/ui/  copied shadcn-vue primitives (button, input, textarea, dialog, dropdown-menu, select,
                  tooltip, skeleton, status-pill, badge, banner, table, tabs, switch, popover)
  components/common/  PageContainer, PageHeader, EmptyState, FileDrop, ConfirmDialog, SafeHtml
  features/chat/      ChatPage.vue, store.ts, api.ts, components/ (MessageList, AnswerMessage, Composer,
                      SourceList, CitationChip), markdown.ts
  features/documents/ DocumentsPage.vue, DocumentDetailPage.vue, store.ts, api.ts,
                      components/ (UploadPanel, DocumentsTable, IngestStatusPill, DocumentMetaDialog)
  features/viewer/    SourcePanel.vue, PdfViewer.vue, ImageViewer.vue, ChunkViewer.vue
  features/usage/     UsagePage.vue, api.ts
  lib/                utils.ts (cn), format.ts, theme.ts, sanitize.ts, colors.ts
  styles/             tokens.css (generated), tailwind.css
```

Each feature owns its `api.ts`, typed from the generated `src/api/schema.d.ts` (`npm run gen:api` reads `backend/openapi.json`, exported by `uv run python -m app.export_openapi`). No hand-written API types. The SSE event payloads are generated too: `export_openapi` adds them to `components.schemas` ([SPEC-08 §6](SPEC-08-api-contract.md)).

## 3. Reuse map (copy, don't reinvent)

| Need | Copy from `office-suite-v2/frontend/` | Change |
|---|---|---|
| Tokens, Tailwind, fonts, focus, scrollbars | `src/styles/tokens.css`, `src/styles/tailwind.css`, `src/assets/fonts/poppins/` | Drop `.rich-text` mention and `.doc-prose` doc styles; add `.answer-prose` (§5.3) |
| Token generator | `scripts/gen-tokens.mjs` | Reads `../docs/design-system.md` (same path) |
| Hex-colour lint rule and lint config | `eslint/no-hex-colors.js`, `eslint.config.ts`, `.prettierrc.json`, `.prettierignore` | Keep the `v-html` ban, with the exception for `SafeHtml.vue` |
| Theme | `src/lib/theme.ts`, `public/theme-init.js` | Storage key `rag-theme` |
| Primitives | `src/components/ui/*` (listed in §2) | None |
| Common components | `src/components/common/PageContainer.vue`, `PageHeader.vue`, `EmptyState.vue`, `FileDrop.vue`, `ConfirmDialog.vue`, `SafeHtml.vue` | `FileDrop`: accept multiple files (emit `files`). `SafeHtml`: no `snippet` prop; always renders through `sanitizeAnswer` (the only allowlist in this app) |
| HTML sanitising | `src/lib/sanitize.ts` | Answer allowlist: `p br strong em code pre ul ol li table thead tbody tr th td h3 h4 blockquote a sup button`; `button` only with `class="citation"`, a numeric `data-cite` and a non-empty `aria-label` (otherwise replaced by its text), and the sanitizer adds `type="button"`; `a` only with `href` (http/https/mailto), and the sanitizer adds `target="_blank" rel="noopener noreferrer nofollow"`. Added attributes are never taken from model output |
| API client | `src/api/http.ts` | Base `/api/v1`; no XSRF, no 401/403 flows; keep `ApiProblem`, `toProblem`, the error toast table, `latestSignal` |
| Layout | `src/app/layouts/AppLayout.vue`, `AppTopBar.vue`, `sidebar.ts` | Nav: Chat, Documents, Usage. Top bar: demo user switcher + theme toggle. Shell: flush sidebar / header / content with borders, no floating page sheet ([design-system §10](../design-system.md#10-components-target-look)). No realtime, no workspace tree |
| Dates, bytes, utils | `src/lib/format.ts`, `src/lib/utils.ts`, `formatBytes` from `src/features/files/api.ts` | Timezone `Asia/Kuala_Lumpur` |
| Build config | `vite.config.ts`, `tsconfig*.json`, `components.json`, `env.d.ts` | Dev port 5173, proxy `/api` and `/health` → `http://localhost:8000`; drop FullCalendar plugin |


## 4. Routes

| Path | Page | Notes |
|---|---|---|
| `/` | → `/chat` | |
| `/chat` | ChatPage | Default |
| `/documents` | DocumentsPage | Upload + list |
| `/documents/:id` | DocumentDetailPage | Metadata, status, chunks, the original |
| `/usage` | UsagePage | Tokens and cost by model and purpose; latest balances |
| `*` | NotFound | Copy `NotFoundPage.vue` |

## 5. Chat

### 5.1 Layout
- `PageContainer width="reading"` for the thread; the **SourcePanel** opens on the right (`item-panel-w` 600px, resizable 480–960) on ≥ 1280px, as an overlay with scrim below that, full screen with a back button on phones (design-system §11 item-panel rules).
- Empty state: title "Ask about company documents", 4 example questions as secondary buttons (Serimaju: leave per application, M2 annual leave, claim deadline, year-end closure in Malay).

### 5.2 Composer
- `Textarea` that grows to 6 lines; Enter sends, Shift+Enter adds a line; max 1,000 characters with a counter after 800.
- While streaming, the primary button becomes **Stop** (aborts the fetch). One primary button per view.

### 5.3 Answer rendering
- Text arrives via `delta` and is rendered with `markdown-it` (`html: false`, `linkify: false`, `typographer: false`), then sanitized and shown through `SafeHtml` in an `.answer-prose` block.
- A markdown-it inline rule turns `[n]`, `[n][m]` and `[n, m]` into one `<button class="citation" data-cite="n" aria-label="Source n: {title}">n</button>` per number, but only for `n` within `1…sources.length`; other numbers stay plain text. Clicks are handled by event delegation on the message container (no Vue bindings inside `v-html`).
- On `done` with `finalText`, the streamed text is replaced and discarded (it is not kept in the store or `sessionStorage`).
- Under the answer: **Sources** — cited sources as cards (title, heading path, page/section/sheet, effective date, file-type icon). Then a collapsed "Other sources searched (k)" list.
- Not found (`found = false`): the answer shows in an `info` Banner with the contact. No source cards.
- Model and latency show as a `caption` line under the answer ("nemo-super · 2.1 s").

### 5.4 SourcePanel
- Originals (`GET /documents/{id}/file`) are always fetched through `http.ts`, which sends `X-Demo-User`, as a `Blob`. pdf.js gets the bytes, images get a `URL.createObjectURL` URL (revoked on close), and **Download original** saves the blob. A plain `<img src>` or `<a href>` to the API can't send the header and would get 401.
- **PDF:** `pdfjs-dist` renders the original (`GET /documents/{id}/file`) and scrolls to `pageStart`; the chunk text is shown above the page as a highlighted quote (no in-page text highlight in the MVP).
- **PNG/JPG:** the image, zoomable (copy `ImageLightbox.vue`), with the extracted text below.
- **DOCX/MD/XLSX:** `ChunkViewer` shows the chunk text (Markdown tables rendered), heading path and neighbouring chunks (`GET /documents/{id}/chunks?around=<chunkId>`), plus a **Download original** button.
- Header: title, status pill (current/superseded), effective date, "Open document" link to `/documents/:id`.

### 5.5 Errors
- `error` event or HTTP problem: show an inline `danger` Banner in the answer slot with the user-facing message ([SPEC-06 §5](SPEC-06-ai-providers.md)) and a **Retry** button. `quota_exhausted` uses `warning` tone and no Retry.
- Lost connection mid-stream: keep the partial text, add "The answer was cut off." and Retry.

### 5.6 State
- `useChatStore`: `messages[]` (`question`, `answer`, `sources`, `cited`, `found`, `status: streaming|done|stopped|error`, `model`, `latencyMs`), `send(question)`, `stop()`, `retry(id)`, `clear()`. The thread is kept in memory and `sessionStorage` (cleared by **New chat**). The last 4 turns go as `history`.

## 6. Documents

### 6.1 Upload
- `UploadPanel` with `FileDrop` (multiple), accepting `.pdf,.docx,.xlsx,.md,.png,.jpg,.jpeg`, max from `GET /config`. Each file uploads in turn with progress; a duplicate (`409`) shows "Already uploaded as *{title}*" with a link.
- Optional fields in a collapsible "Details" section, applied to all files in the batch: title (single file only), document type, department, effective date, access groups (multi-select from the caller's own groups in `GET /me`, since uploads may only use those).

### 6.2 List
- `DataTable` columns: Title (with file-type icon, truncates), Type, Department, Effective (formatted), Status (`StatusPill`: current → green, superseded → grey), Ingestion (`IngestStatusPill`: queued → grey, processing → blue with a spinner icon, ready → green, failed → red with the error in a tooltip), Chunks, Access (chips, at most 2 then `+n`), Uploaded.
- Filters (segmented tabs): All · Current · Superseded · Failed. Search by title (client-side).
- Row actions (fade in on hover/focus): Open, Re-ingest, Mark superseded / Mark current, Edit details, Delete (ConfirmDialog with danger button).
- Polls `GET /documents` every 3 s while any row is `queued` or `processing`; stops otherwise.
- Phones: card list instead of the table (design-system §11).

### 6.3 Detail
- Header: title, pills, actions. Metadata list. Ingestion error banner with Retry when failed.
- Tabs (underline): **Chunks** (ordinal, type, heading path, page/sheet, tokens, expandable text) · **Original** (PDF/image viewer, or Download).

## 7. Usage page
- Two stat rows: questions (count, avg latency, avg tokens) and ingestion (documents, chunks, embedding tokens).
- Table by model × purpose: calls, prompt tokens, completion tokens, cost (MYR or "plan quota").
- Latest balances: plan tokens left, PAYG MYR left (from the provider headers), with the time read.

## 8. Demo identity
- Top-bar `Select` lists demo users from `GET /config` (e.g. *Aisyah (HR)*, *Ben (Staff)*). `/config` is the one `/api/v1` call made without `X-Demo-User`, because it runs before a user is chosen. The choice is stored in `localStorage` and sent as `X-Demo-User` on every request ([SPEC-09 §3](SPEC-09-security-and-access.md)). Changing user clears the chat thread and reloads documents.

## 9. Accessibility and states
- Every page has loading (Skeleton rows), empty, error and success states. No spinners in tables except the processing pill icon.
- The answer region is `aria-live="polite"` and announces only on `done` (not per delta).
- Citation buttons have `aria-label="Source n: {title}"`.
- Keyboard: `/` focuses the composer; `Esc` closes the SourcePanel.

## 10. Testing
- Vitest + `@vue/test-utils` with jsdom, as in Office Suite. SSE parsing, the citation markdown rule, sanitizing, stores and status pills are unit-tested.
- Fixtures mode: `VITE_USE_FIXTURES=1` makes `features/*/api.ts` return fixtures from `src/fixtures/` (a recorded SSE stream included), so UI work can start before the backend endpoints exist.

## 11. Acceptance checks

1. The SSE reader parses `meta`, `sources`, `delta`, `done` and `error` events split across arbitrary chunk boundaries.
2. `[1]`, `[2][3]` and `[2, 3]` render as citation buttons; `[9]` with 3 sources stays plain text; `<script>` and `onerror=` in model text never reach the DOM.
3. Clicking a citation opens the SourcePanel for that source; a PDF source opens at `pageStart`.
4. `done.finalText` replaces the streamed text.
5. A not-found answer renders as an info banner with the contact and no source cards.
6. `quota_exhausted` renders a warning banner without Retry; other errors show Retry.
7. Stop aborts the request and leaves the partial answer marked as stopped.
8. The documents list polls while a row is queued/processing and stops when none are.
9. Uploading a duplicate shows the "Already uploaded" message with a link.
10. No hex colours in `src/` (lint), and every page renders in light and dark themes without contrast regressions (manual check in the walkthrough).
11. The SourcePanel image viewer and **Download original** fetch the file with `X-Demo-User` (no direct `src`/`href` to `/api/v1/documents/{id}/file`).
