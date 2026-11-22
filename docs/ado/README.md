# Azure DevOps backlog (mock)

This folder is a **mock Azure DevOps backlog** for the Company Docs Assistant. It shows the starting point of the team workflow: a project manager writes stories in ADO, and the specs and milestones in this repo are built from them.

| File | What it is |
|---|---|
| [E1000-company-docs-assistant.md](E1000-company-docs-assistant.md) | The epic: problem, goals, feature list |
| [features/](features/) | One file per feature with its user stories, as a developer would copy them out of ADO |
| [TRACEABILITY.md](TRACEABILITY.md) | Story → spec sections → milestones |
| [ado-import.csv](ado-import.csv) | The same backlog as a CSV you can import into a real ADO project |
| [gen_backlog.py](gen_backlog.py) | The data and generator behind the files above |

The work item IDs (1000, 1101…) are mock numbers. A real import assigns new ones.

## The workflow

```
1. PM          writes Epic → Features → User Stories in ADO (business language, acceptance criteria, open questions)
2. Developer   picks a feature, copies its stories (or the AI reads them through an ADO connection) into Claude Code
3. AI          drafts or updates the specs: turns business criteria into numbered spec sections and acceptance checks,
               answers the PM's open questions as decisions or open items, and adds the story → spec rows to TRACEABILITY.md
4. Developer   reviews the specs (the human gate) and sends questions back to the PM in the story's discussion
5. AI          writes the milestones, each one naming the stories it delivers and the spec sections to read
6. AI agents   build milestone by milestone; spec checks become named tests; deviations are logged
7. Developer   reviews the milestone, links commits/PRs to the stories (AB#1101 / #1101), and moves the stories to Resolved
```

The PM's stories stay the **what and why**. The specs hold the **how**, and they are the source of truth for the code. When a story changes in ADO, the developer repeats steps 2–5 for the affected sections only.

**Useful example for the presentation:** story 1203 (*Read Excel spreadsheets correctly*) says only that rows must be understood with their headers. [SPEC-03 §5.2](../specs/SPEC-03-ingestion.md) turns that into header detection, 20-row chunks with repeated headers, `Header: value` lines and cached formula values. Acceptance check 6 then becomes a test named `test_spec03_ac06_…`.

## Importing into Azure DevOps

1. Create a project with the **Agile** process. The CSV uses *User Story* and *Story Points*; for the Scrum process, rename *User Story* to *Product Backlog Item* and *Story Points* to *Effort*.
2. Go to **Boards → Queries → Import work items**, choose `ado-import.csv` and select **Import**.
3. The `Title 1 / Title 2 / Title 3` columns create the Epic → Feature → User Story hierarchy. Check the preview, then **Save items**.
4. Set the Area and Iteration paths afterwards. They aren't in the CSV because they must already exist in the project.

## Regenerating

The Markdown, CSV and trace map are generated from the data in [gen_backlog.py](gen_backlog.py), so they always agree. To change a story, edit the data there and run `python docs/ado/gen_backlog.py`. Don't hand-edit the generated files.
