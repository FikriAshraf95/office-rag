# Feature 1600 — Platform and operations

> **Mock Azure DevOps export.** Parent: Epic 1000 — Company Docs Assistant · Created by Nurul Huda (PM) · State: New · 3 stories, 14 points

The system is easy to run, move to another AI provider, and later preview online.

## User Story 1601 — Run the whole system with one command

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 1 | 3 | Sprint 2026-11 (19–26 Nov) | mvp |

**As a** developer, **I want** to start everything with one command on a clean machine, **so that** anyone on the team can run the demo.

**Acceptance criteria**

1. One command starts the whole system; the README explains the steps.
2. It works on a clean machine with only the API key added.

## User Story 1602 — Switch AI provider without code changes

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 2 | 3 | Sprint 2026-11 (19–26 Nov) | mvp |

**As a** IT manager, **I want** to move from ILMU to another provider (e.g. Azure AI Foundry) by configuration, **so that** production isn't locked to the demo provider.

**Details**

- ILMU is for the demo only. Production will likely run on Azure.

**Acceptance criteria**

1. Changing provider needs configuration only, plus a documented re-indexing step.
2. The test set must pass on the new provider before go-live.

**Questions for the developers**

- Which Azure region would we use?

## User Story 1603 — Public preview over the internet

| Priority | Story points | Iteration | Tags |
|---|---|---|---|
| 3 | 8 | Backlog | post-demo; security |

**As a** product manager, **I want** invited people to try the assistant from anywhere, **so that** we can collect feedback after the demo.

**Details**

- After the 26 Nov presentation. Still fictional documents only. Planned with Cloudflare Tunnel.

**Acceptance criteria**

1. Only invited emails can sign in.
2. Only admins can upload or change documents.
3. Each person has a daily question limit so the AI budget is protected.
4. No ports are opened on the office/home network.
