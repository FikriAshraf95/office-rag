# Enhancements log

Ideas to extend the project or the SDD workflow. They are **not** part of the current milestones. Each one has enough context to pick up later without the original conversation.

Status: **Idea** → **Planned** (has a milestone or task) → **Done** (date, where) · or **Dropped** (why).

| # | Enhancement | Status | Effort | Best time |
|---|---|---|---|---|
| E1 | [Add ADO story IDs to the specs and milestones](#e1--add-ado-story-ids-to-the-specs-and-milestones) | Idea | ~30 min | Before M00 starts, or during M99 |
| E2 | [Connect Claude Code to Azure DevOps through MCP](#e2--connect-claude-code-to-azure-devops-through-mcp) | Idea | ½–1 day | After the presentation (it would make a good demo slide if done earlier) |
| E3 | [Full dev container for the team](#e3--full-dev-container-for-the-team) | Idea | ½ day | When other developers adopt the template |

---

## E1 — Add ADO story IDs to the specs and milestones

**Added:** 2026-11-19 · **Status:** Idea

**Why:** [docs/ado/TRACEABILITY.md](../docs/ado/TRACEABILITY.md) maps stories to specs and milestones in one place. Agents and reviewers read the specs and milestones, though, not the trace file. With the IDs in those files, the link from story to spec to code is visible where the work happens, and commits can mention the story.

**What:**
- Each milestone header gets one line: `> **Stories:** 1101, 1102, 1105` (taken from the trace map).
- SPEC-00 gets a short **Source stories** section: the epic and feature IDs, and a pointer to `docs/ado/`.
- Optional: each spec's header gets `**Stories:** …` for the stories it implements.
- Root CLAUDE.md gets one rule: *"Commits and PRs reference the milestone and its stories: `M03: hybrid search (#1304, #1401)`."* In Azure Repos, `#<id>` links the work item; from GitHub it is `AB#<id>`.

**How:** generate the lines from the data in [docs/ado/gen_backlog.py](../docs/ado/gen_backlog.py) (it already holds the story → milestone map), so the IDs stay in step with the trace file. Keep root CLAUDE.md within about 5 KB.

**Done when:** every milestone file names its stories, the trace map and the headers agree, and the commit rule is in CLAUDE.md.

**Presentation angle:** one slide that follows story 1203 → SPEC-03 §5.2 → M02 → `test_spec03_ac06_…` → commit `#1203`.

---

## E2 — Connect Claude Code to Azure DevOps through MCP

**Added:** 2026-11-19 · **Status:** Idea

**Why:** in today's workflow the developer copies stories out of ADO into Claude Code by hand (step 2 in [docs/ado/README.md](../docs/ado/README.md)). An MCP connection lets the agent read the feature, its stories and their comments directly, and later post questions back or move the state. Copy-paste mistakes disappear and the loop closes inside ADO, which supports the "standardize the team" goal.

**What it could do, in order of risk:**
1. **Read only:** fetch an epic, feature or story with its acceptance criteria and discussion → draft or update specs.
2. **Comment:** post the developer-approved open questions to the story's discussion for the PM.
3. **Write:** link commits and PRs, and set the state (Active → Resolved) when a milestone is DONE. Only after a human approves.

**How (verify everything before relying on it — not checked yet):**
- Microsoft publishes an Azure DevOps MCP server (GitHub `microsoft/azure-devops-mcp`). A remote, hosted version may also be available. Check the current README for the install command, auth (Entra ID / `az login` vs a PAT), and which tool groups (work items, repos, pipelines) can be enabled.
- Add it to Claude Code at the project scope (`claude mcp add …`, or `.mcp.json` in the repo) so every developer gets the same setup. Enable only the **work items** tools at first.
- Allowlist the read tools in `.claude/settings.json` and leave write tools behind a permission prompt.
- Add a short section to root CLAUDE.md: which ADO project/area to read, how to map a feature to specs (step 3 of the workflow), and "never change a work item's state without the developer's approval".
- Try it on a real ADO project: import [docs/ado/ado-import.csv](../docs/ado/ado-import.csv), then ask Claude Code to "read Feature 1200 and list which SPEC-03 sections cover each story".

**Risks and guardrails:**
- **Story text is untrusted input.** A story or comment can contain prompt-injection text. Treat it as data, review generated specs as usual, and keep write tools on approval.
- Use a credential with the **least scope** (work items read, plus write only when needed) and never commit it. Prefer the user's own sign-in over a shared PAT.
- Company policy: confirm ADO data may be sent to the AI provider in use (same question as for documents).

**Done when:** a developer can go from an ADO feature to updated specs without copy-paste, and the agent can post a question back to a story after approval.

**Presentation angle:** a live or recorded demo: "read Feature 1300" → spec diff → reviewer approves → the question appears in the ADO story.

---

## E3 — Full dev container for the team

**Added:** 2026-11-19 · **Status:** Idea (deferred in favour of the hybrid setup for this build)

**Why:** this build uses a hybrid setup: Postgres in Docker, and the API, worker and frontend on the host with uv-managed Python 3.14. That is fastest on Windows. For a team template, a dev container gives every developer the same tools with one click.

**What:** a `.devcontainer/` (VS Code Dev Containers) with Python 3.14 + uv, Node 22, and Postgres as a Compose sidecar, with the commands in CLAUDE.md working unchanged inside it.

**Watch out:** on Windows, keep the repo **inside the WSL2 filesystem**. Docker Desktop bind mounts from `D:\` are slow, and file watching for `--reload` and Vite gets unreliable.

**Done when:** a new developer clones, opens the folder in the dev container, and runs the backend tests and frontend build without installing anything else.
