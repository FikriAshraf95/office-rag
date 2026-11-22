# Serimaju Demo Documents: RAG test set

A **fully fictional** document set for a made-up Malaysian tech startup, **Serimaju Technologies Sdn Bhd**, whose clients are a bank, a manufacturer and an asset manager. Use it to build and evaluate the company-docs RAG system before touching real company data. Every document carries a "FICTIONAL, FOR RAG TESTING ONLY" marker. Names, emails (`*.example`) and figures are invented.

## Folder layout

```
documents/   ← ingest these into the RAG system
eval/        ← evaluation questions with expected answers (do NOT ingest)
FACT_SHEET.md← ground truth the documents were generated from (do NOT ingest)
```

## Documents (10 files, 6 formats)

| File | Format | What it tests |
|---|---|---|
| `HR_Employee_Handbook_2026.pdf` | PDF, 4 pages, headings + tables | Main policy source |
| `HR_Employee_Handbook_2024.pdf` | PDF, marked SUPERSEDED | **Version trap:** older, different values |
| `Memo_HR_2026-09_Leave_Policy_Amendment_scan.png` | Scanned-looking image (noise, slight tilt, stamp) | **OCR + override trap:** changes the handbook's leave limits |
| `Leave_Entitlement_by_Grade_2026.xlsx` | Excel, 3 sheets incl. a formula calculator | Table lookups by grade × service |
| `Client_Accounts_Q4_2026.xlsx` | Excel, accounts + projects with formulas | Lookups and aggregation (team sizes) |
| `IT_Security_Policy_v3.docx` | Word, numbered sections + table | Structured DOCX |
| `Client_Engagement_and_Data_Handling_Policy.docx` | Word | Client-specific rules (bank / factory / asset manager) |
| `Travel_and_Claims_SOP.md` | Markdown with YAML frontmatter | Simple baseline + table |
| `Org_Chart_2026.jpg` | Image (diagram) | **Vision:** reporting lines |
| `Notis_Penutupan_Akhir_Tahun_2026_Year_End_Closure.pdf` | PDF, Malay + English | **Multilingual** retrieval and answering |

## Deliberate traps

1. **Superseded document:** the 2024 handbook has different numbers for almost everything. Answers must come from the 2026 handbook.
2. **Memo overrides handbook:** the scanned memo raises the leave limit per application from 7 to **10** days (from 1 Oct 2026) and extends the 2026 carry-forward deadline to **30 April 2027**.
3. **Answer only in an image:** reporting lines exist only in the org chart; the memo exists only as a scan.
4. **Multi-hop:** e.g. remote work abroad is allowed (handbook) but not for Bank Teratai systems (client policy).
5. **Malay question:** Q28 is asked in Malay and should be answered in Malay.
6. **Not in any document:** ESOS vesting and pets. The system must say it can't find these, not guess. Q32 (office parking) looks similar but *is* answered.

## Evaluation

`eval/eval_questions.csv` has 32 questions with columns `id, question, expected_answer, expected_sources, category, notes`. Suggested scoring per question:
- **Correct** (1): right facts, current version, cites the expected source.
- **Partial** (0.5): right facts but missing a condition, or weak citation.
- **Wrong** (0): wrong or outdated value, or a guess on a not-found question.

Re-run after every change (chunking, embeddings, reranker, prompt). The score trend makes a great presentation slide.

## Tips for ingestion tests
- The memo PNG needs OCR or a vision model; plain text extraction returns nothing.
- Excel: keep column headers with every row chunk ("Manager | More than 5 years | 22").
- Version handling: the 2024 handbook says "SUPERSEDED" on page 1. Store that as metadata (`status: superseded`) and filter it out, rather than relying on the LLM to notice.
