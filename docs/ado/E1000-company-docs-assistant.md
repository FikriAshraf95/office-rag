# Epic 1000 — Company Docs Assistant

> **Mock Azure DevOps export.** Created by Nurul Huda (PM) · State: New

Staff lose time hunting for policy answers in handbooks, memos and spreadsheets, and often find an outdated version.
We want an internal assistant that answers questions **only from our own documents**, shows where every answer comes from, and says so when it doesn't know. A wrong policy answer is worse than no answer.
First release is a **demo for the engineering all-hands on 26 Nov 2026**, using the fictional *Serimaju Technologies* document set (no real company documents). The build itself is also our case study for AI-assisted development.

**Goals**

- At least 26 of the 32 test questions answered correctly.
- Answers start appearing within about 3 seconds.
- Restricted documents never leak to people outside their group.
- Runs on one machine with one command.

**Features**

- [Feature 1100 — Document library](features/F1100-document-library.md): Document owners can add, review, correct and remove the documents the assistant answers from.
- [Feature 1200 — Document processing](features/F1200-document-processing.md): Uploaded documents are read correctly, whatever their format, so answers can quote the right section, page or table row.
- [Feature 1300 — Ask questions](features/F1300-ask-questions.md): Staff ask questions in a chat and get short, sourced answers they can trust.
- [Feature 1400 — Access and security](features/F1400-access-and-security.md): People only ever see documents they are allowed to see, and the system is safe to run.
- [Feature 1500 — Answer quality, usage and cost](features/F1500-quality-and-cost.md): We can prove how good the answers are and what they cost.
- [Feature 1600 — Platform and operations](features/F1600-platform-and-operations.md): The system is easy to run, move to another AI provider, and later preview online.
