# Frontend rules (`frontend/`)

Vue 3 `<script setup lang="ts">`, strict TypeScript, Pinia, Vue Router, Tailwind v4 + shadcn-vue (reka-ui), lucide icons, vue-sonner. Spec: [SPEC-07](../docs/specs/SPEC-07-frontend.md). Look: [design-system.md](../docs/design-system.md).

## Copy, don't reinvent
The UI kit comes from **Office Suite v2** (`D:\fikri\onedrive\demo\office-suite-v2-feature-uiux-revamp\frontend`). Before writing a component, check SPEC-07 §3 and copy the Office Suite file. Change only what the "Change" column says. Never pull in Office Suite features outside that table (SignalR, boards, tiptap, auth store).

## Rules
- Features live in `src/features/<name>/` with their own `api.ts`, typed from the **generated** `src/api/schema.d.ts` (`npm run gen:api`). No hand-written API types, no global API file.
- HTTP through `src/api/http.ts`; chat streaming through `src/api/sse.ts` (fetch + ReadableStream, never `EventSource`). Branch on `ApiProblem.code`, never on `detail`.
- Every request sends `X-Demo-User` (set in `http.ts` / `sse.ts` from the user store).
- **No raw colours.** Tokens only (`bg-surface`, `text-ink-muted`, `bg-label-green-soft`…); ESLint rejects hex. Token changes go through `docs/design-system.md` → `npm run gen:tokens`.
- `v-html` is banned except in `SafeHtml.vue`. Model output: markdown-it with `html: false` → `sanitizeAnswer()` → `SafeHtml`. Citation buttons are handled by event delegation (`data-cite`).
- One primary button per view. Sentence case, no emoji, errors say how to fix the problem.
- Every page has loading (Skeleton), empty, error and success states. Pages sit in `PageContainer` (`wide` for documents/usage, `reading` for chat).
- Dates via `lib/format.ts` in `Asia/Kuala_Lumpur`.
- Tests: Vitest, colocated `*.test.ts`, named after SPEC-07 §11 checks (`it('Spec07_Ac01 …')`).
- Fixtures mode: `VITE_USE_FIXTURES=1` — keep fixtures in `src/fixtures/` in sync with SPEC-08 shapes.

## Commands
`npm run dev` (5173, proxies `/api` → :8000) · `npm run lint` · `npm run typecheck` · `npm run test` · `npm run build` · `npm run gen:api` · `npm run gen:tokens`
