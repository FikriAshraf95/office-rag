# IDEA — Company Docs RAG

> **Locked:** 2026-11-19. Changes go through the specs ([SPEC-00](specs/SPEC-00-overview.md)); this file only records the idea.

## What

Users upload company documents (PDF, DOCX, XLSX, Markdown, PNG/JPG/JPEG). The system extracts, chunks, embeds and stores them. Users ask questions in a chat UI. Answers are **grounded in the documents** and carry **citations** to the exact source and page or section. Clicking a citation opens the source at that place.

> "What's the maximum leave I can take per application?" → "Up to 10 consecutive working days per application from 1 Oct 2026; longer needs HOD and HR approval. [1][2]" → [1] Memo HR 2026-09, [2] HR Handbook 2026 §4.2, p.2.

If nothing relevant is found, it says so and suggests who to contact. **It never guesses**: a wrong policy answer is worse than none.

## Who

- **Staff** ask questions about policies, SOPs, entitlements and clients.
- **Document owners / admins** upload documents, watch ingestion, and mark old versions as superseded.
- **The development team** sees a real case study of spec-driven development (SDD) with Claude Code: an Opus orchestrator plus Sonnet subagents.

## Why

1. Staff lose time hunting through handbooks, memos and spreadsheets, and often find the outdated version.
2. The user's boss asked for a presentation of the SDD workflow so the team can standardize on it. This project is that presentation's case study. **The presentation is on 2026-11-26.**

## Scope for the demo

- Runs on the fictional **Serimaju** sample set (`samples/serimaju/`) with **ILMU AI** (Malaysia-hosted, OpenAI-compatible). No real company documents.
- The design leaves room for a production move to another OpenAI-compatible provider or Azure AI Foundry, by config and a re-embed, without code changes.

## Non-goals (for this build)

- SSO and real user management (a demo user switcher stands in; `access_groups` are enforced at retrieval anyway).
- Sync from SharePoint or Google Drive.
- Editing documents in the app.
- Multi-tenant hosting, or hosting real company data on a personal machine.
- LangChain or LlamaIndex: the pipeline is thin custom code that developers and agents can trace.
