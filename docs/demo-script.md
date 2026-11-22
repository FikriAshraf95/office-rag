# Demo script (SDD presentation, 2026-11-26)

About 8 minutes. Seven questions (rehearsed end to end on the full stack on 2026-11-22: all seven as expected), each showing one thing a naive RAG gets wrong. Run on the full stack at `http://localhost:8080` with the reranker on (`RERANK_MODEL=bge-reranker`).

## Before the talk

1. `docker compose down -v && docker compose up -d --build` (fresh database). Wait for `docker compose ps` to show `api` and `frontend` healthy.
2. Open `http://localhost:8080`, user **Ben (Staff)** → **Documents** → upload all 10 files from `samples/serimaju/documents/`. Wait for **Ready** on every row (2–4 minutes; the org chart and memo take longest because of OCR and vision).
3. Fix two auto-titles (the parser takes the first heading, which is weak for these two): **Edit details** on *SERIMAJU TECHNOLOGIES SDN BHD* → `HR Memo 2026-09: Leave Policy Amendment`, and on *2026* → `Notis Penutupan Akhir Tahun 2026 (Year-End Closure)`. Citations then show readable names.
4. Switch to **Aisyah (HR)** → upload `backend/tests/fixtures/private_salary_bands.md` with access group **hr** only. Switch back to **Ben**.
5. Check: the 2024 handbook row shows **Superseded**. Run `bash scripts/release_check.sh` (all PASS; it also warms the provider connection), then **New chat**.
6. Keep a second tab on **Usage** for the cost question at the end.

**Click New chat before each question.** A follow-up searches with the previous question plus the new one ([SPEC-05 §1](specs/SPEC-05-answering.md)), which helps "and for managers?" but can dilute a sudden topic change into a not-found answer. In the rehearsal, *office days* asked right after *salary band* was refused; asked fresh it was answered.

## The questions

| # | Ask (as Ben unless noted) | Expected | What it shows |
|---|---|---|---|
| 1 | *What is the maximum number of consecutive working days I can take in one leave application without HOD approval?* | **10 days** (from 1 Oct 2026), citing the **scanned memo** (sometimes also the 2026 handbook §4.2) | **Memo override + OCR.** The handbook says 7; a scanned PNG memo changes it. The answer comes from an image. |
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
- **Answers differ in wording from the table above:** expected. Facts and citations should match; the eval (28.5/32 at M99) is the reference, not a single run.
