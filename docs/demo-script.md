# Demo script (SDD presentation, 2026-11-26)

About 8 minutes. Seven questions, each showing one thing a naive RAG gets wrong. Run on the full stack at `http://localhost:8080` with the reranker on (`RERANK_MODEL=bge-reranker`).

## Before the talk

1. `docker compose down -v && docker compose up -d --build` (fresh database). Wait for `docker compose ps` to show `api` and `frontend` healthy.
2. Open `http://localhost:8080`, user **Ben (Staff)** → **Documents** → upload all 10 files from `samples/serimaju/documents/`. Wait for **Ready** on every row (2–4 minutes; the org chart and memo take longest because of OCR and vision).
3. Switch to **Aisyah (HR)** → upload `backend/tests/fixtures/private_salary_bands.md` with access group **hr** only. Switch back to **Ben**.
4. Check: the 2024 handbook row shows **Superseded**. Ask one warm-up question so the provider connection is warm, then **New chat**.
5. Keep a second tab on **Usage** for the cost question at the end.

## The questions

| # | Ask (as Ben unless noted) | Expected | What it shows |
|---|---|---|---|
| 1 | *What is the maximum number of consecutive working days I can take in one leave application without HOD approval?* | **10 days** (from 1 Oct 2026), citing the **scanned memo** and the 2026 handbook §4.2 | **Memo override + OCR.** The handbook says 7; a scanned PNG memo changes it. The answer comes from an image. |
| 2 | Click the memo's citation `[n]` | The source panel opens the memo image | **Citation click.** Every claim is traceable to a page, section or row. |
| 3 | *How many days of annual leave does a Grade M2 manager with 6 years of service get?* | **22 days**, citing *Leave_Entitlement_by_Grade_2026.xlsx*. Click the citation: the sheet and rows are shown | **Table lookup.** Spreadsheet rows are chunked with their header repeated, so "M2 × 6 years" matches exactly. |
| 4 | *How many days a week must I work from the office, and which days?* | **3 days: Tuesday, Wednesday, Thursday** (2026 handbook) | **Superseded filter.** The 2024 handbook says 2 days and is never searched: it is filtered out in SQL before ranking, not left for the model to notice. |
| 5 | *Adakah saya perlu mengambil cuti tahunan pada 29 Disember 2026?* | **Tidak**, answered in Malay: 29 Dec is company leave; annual leave only on 28 and 31 Dec | **Malay.** Malay question, bilingual source, Malay answer. |
| 6 | *Can I bring my dog to the office?* | "I can't find this in the documents you have access to", suggesting HR (hr@serimaju.example). No LLM call | **Not found.** The relevance gate stops weak matches before the model; the answer never guesses. |
| 7 | *What is the salary band for an M2 manager?* — as **Ben**, then switch to **Aisyah (HR)** and ask again | Ben: not found. Aisyah: **RM 9,000 – 13,500**, citing *Salary bands 2026 (restricted)* | **Access groups.** The restricted document is filtered by group inside both search arms, before ranking. For Ben it doesn't exist: not in search, chat, the document list, or by direct URL. A test suite checks that the marker `ZQX-PRIVATE-7` never reaches him. |

Optional if time allows: *Who does the Finance team report to?* (org chart read by the vision model; **Kumar Selvam, Finance Manager, who reports to CFO Hafiz Osman**).

## Closing numbers

Open **Usage**: tokens and cost per question (see [presentation numbers](../presentation-notes/numbers.md)).

## If something goes wrong

- **An answer says the AI service is busy:** ILMU rate limit; wait 30 s and ask again.
- **A document stays Processing:** `docker compose logs worker --tail 50`. Re-ingest from the document's menu.
- **Answers differ in wording from the table above:** expected. Facts and citations should match; the eval (28/32) is the reference, not a single run.
