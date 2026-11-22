# M05 — Frontend: chat, sources and documents

> **Depends on:** [M00](M00-foundation.md) (fixtures mode); M01–M04 for the live walkthrough · **Blocks:** [M99](M99-release-and-demo.md)
> **Read first:** [SPEC-07 (whole file)](../specs/SPEC-07-frontend.md) · [SPEC-05 §6](../specs/SPEC-05-answering.md#6-sse-events) · [SPEC-08 §2, §4, §6–7](../specs/SPEC-08-api-contract.md#2-error-shape) · [design-system §8, §10–11](../design-system.md#8-states--motion)
> **Model:** Sonnet. The kit already exists; this is assembly against a precise spec. Can run in a **parallel session** from M02 onward with frontend-only file ownership.

## Goal
The chat page streams answers with clickable citations that open the source (PDF at the page, image, or chunk text), handles not-found and errors clearly, and the documents pages from M01–M02 are polished. A usage page shows tokens and cost. Everything works in fixtures mode and against the live API.

## Tasks
### Frontend
- [x] `api/sse.ts`: POST + `ReadableStream` reader, event parser, `AbortController`.
- [x] `features/chat`: store, `ChatPage`, `MessageList`, `AnswerMessage` (markdown-it + citation rule + SafeHtml + delegation), `Composer` (Enter/Shift+Enter, Stop), `SourceList`, empty state with example questions, error and not-found banners.
- [x] `lib/sanitize.ts` answer allowlist; `.answer-prose` styles in `tailwind.css` (tokens only).
- [x] `features/viewer`: `SourcePanel` (responsive per design-system §11), `PdfViewer` (pdfjs-dist, worker via Vite `?url`), `ImageViewer`, `ChunkViewer`.
- [x] `features/usage/UsagePage`.
- [x] Fixtures mode (`VITE_USE_FIXTURES=1`) with recorded SSE.
- [x] Phone layouts: documents card list, full-screen SourcePanel.
### Tests
- [x] SPEC-07 §11 checks 1–7, 10 (lint part).

## Acceptance criteria
1. The tests above are green, along with the full gates (lint, typecheck, test, build).
2. **Walkthrough (live stack):** ask Q01 → tokens stream, citations [1][2] are buttons; click [1] → memo image opens with its text; click the handbook citation → PDF opens at page 2; ask Q30 → info banner with HR contact; press Stop mid-answer; switch to dark theme and phone width (DevTools) and repeat one question.
3. **Deviations recorded**, or *"Deviations: none"*.

**Status:** IMPLEMENTED (2026-11-21), not yet DONE. Gates green: lint, typecheck, 91 tests (SPEC-07 §11 checks 1–7 incl. 11's blob fetch), build. **Pending:** the live-stack walkthrough (acceptance 2) and the light/dark/phone visual check. Deviations: none logged (ImageViewer adapts Office Suite's `ImageLightbox` to an inline, Blob-fed viewer so no direct URL hits the API — log as a deviation if you want that strict).
