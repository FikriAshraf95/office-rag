"""Generates mock Azure DevOps backlog files for office-rag: Markdown per feature, a CSV import, a trace map."""
import csv
import html
import pathlib
import sys

OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).parent
PM = "Nurul Huda (PM)"
SPRINT = "Sprint 2026-11 (19–26 Nov)"
LATER = "Backlog"

EPIC = {
    "id": 1000,
    "title": "Company Docs Assistant",
    "description": [
        "Staff lose time hunting for policy answers in handbooks, memos and spreadsheets, and often find an outdated version.",
        "We want an internal assistant that answers questions **only from our own documents**, shows where every answer comes from, and says so when it doesn't know. A wrong policy answer is worse than no answer.",
        "First release is a **demo for the engineering all-hands on 26 Nov 2026**, using the fictional *Serimaju Technologies* document set (no real company documents). The build itself is also our case study for AI-assisted development.",
    ],
    "goals": [
        "At least 26 of the 32 test questions answered correctly.",
        "Answers start appearing within about 3 seconds.",
        "Restricted documents never leak to people outside their group.",
        "Runs on one machine with one command.",
    ],
}

# Each story: id, title, user, want, so, details (list), ac (list of Given/When/Then or bullets),
# priority 1-4, points, tags, questions (PM's open questions for dev), trace (spec refs), milestones
FEATURES = [
    {
        "id": 1100, "slug": "document-library", "title": "Document library",
        "summary": "Document owners can add, review, correct and remove the documents the assistant answers from.",
        "stories": [
            dict(id=1101, title="Upload documents", user="document owner",
                 want="upload PDF, Word, Excel, Markdown and image files, several at once",
                 so="staff can ask questions about them",
                 details=["Supported: PDF, DOCX, XLSX, MD, PNG, JPG/JPEG.",
                          "Optional details on upload: title, document type, department, effective date, who can see it."],
                 ac=["Given I select several supported files, when I upload them, then each appears in the list straight away and I don't have to wait for processing.",
                     "Given a file is over the size limit, when I upload it, then I see a message with the limit and nothing is saved.",
                     "Given a file type we don't support, when I upload it, then I'm told which types are allowed.",
                     "Given the exact same file was already uploaded, when I upload it again, then I'm told it already exists, with a link to it.",
                     "Given I set \"who can see it\", then I can only choose groups I belong to myself."],
                 priority=1, points=5, tags="mvp",
                 questions=["What should the size limit be? 25 MB feels enough for policies.",
                            "Can we spot a duplicate even if the file was renamed?"],
                 trace=["SPEC-03 §2", "SPEC-09 §2", "SPEC-08 §4.1", "SPEC-07 §6.1"], ms=["M01", "M05"]),
            dict(id=1102, title="See all documents and their processing status", user="document owner",
                 want="see every document with its details and whether it is ready to answer questions",
                 so="I know when the assistant can use it and spot problems",
                 details=["Columns: title, type, department, effective date, current/old version, processing status, who can see it, uploaded date."],
                 ac=["Processing status shows as Queued, Processing, Ready or Failed, and updates on its own without refreshing the page.",
                     "Failed documents show the reason in plain words.",
                     "I can filter to All, Current, Old versions or Failed, and search by title.",
                     "On a phone the list is readable without scrolling sideways."],
                 priority=1, points=3, tags="mvp",
                 questions=[], trace=["SPEC-07 §6.2", "SPEC-08 §4.2"], ms=["M01", "M05"]),
            dict(id=1103, title="Correct document details and mark old versions", user="document owner",
                 want="edit a document's details and mark it as replaced by a newer version",
                 so="the assistant never answers from an outdated policy",
                 details=["Example: HR Handbook 2024 is replaced by HR Handbook 2026."],
                 ac=["I can change title, type, department, effective date, version and who can see it.",
                     "When I mark a document as an old version, then from that moment it is never used in answers.",
                     "I can mark it as current again, and it is used again.",
                     "Changing who can see a document takes effect immediately everywhere."],
                 priority=1, points=3, tags="mvp",
                 questions=["Should uploading a document with the same title replace the old one automatically?"],
                 trace=["SPEC-03 §1, §6.1", "SPEC-08 §4.3", "SPEC-07 §6.2"], ms=["M01"]),
            dict(id=1104, title="Delete a document", user="document owner",
                 want="delete a document I uploaded by mistake",
                 so="it is no longer shown or used",
                 details=[],
                 ac=["I must confirm before it is deleted.",
                     "After deleting, it disappears from the list and is never used in answers again.",
                     "The stored file is removed too."],
                 priority=2, points=2, tags="mvp", questions=[],
                 trace=["SPEC-03 §7", "SPEC-08 §4.4"], ms=["M01"]),
            dict(id=1105, title="Open a document and see what the system read from it", user="document owner",
                 want="open the original file and see the text the system extracted",
                 so="I can check it was read correctly",
                 details=[],
                 ac=["PDFs and images open in the browser; other files can be downloaded.",
                     "I can see the extracted pieces in order, with their headings and page numbers.",
                     "If processing failed, I can retry from this page."],
                 priority=2, points=3, tags="mvp", questions=[],
                 trace=["SPEC-07 §6.3", "SPEC-08 §4.5, §4.7"], ms=["M01", "M02"]),
        ],
    },
    {
        "id": 1200, "slug": "document-processing", "title": "Document processing",
        "summary": "Uploaded documents are read correctly, whatever their format, so answers can quote the right section, page or table row.",
        "stories": [
            dict(id=1201, title="Process documents in the background", user="document owner",
                 want="documents to be processed automatically after upload",
                 so="I don't have to wait, and chat stays fast for everyone",
                 details=["The AI service has a monthly plan quota and a pay-as-you-go balance. Running out must be handled gracefully."],
                 ac=["Upload returns immediately; processing happens separately and does not slow down chat.",
                     "If the AI service is briefly busy, processing retries by itself.",
                     "If the AI quota or balance is used up, the document shows Failed with a message saying so, and does not keep retrying. I can retry it later.",
                     "If the system restarts during processing, the document is picked up again."],
                 priority=1, points=8, tags="mvp",
                 questions=["How many documents can we process at the same time?"],
                 trace=["SPEC-03 §3", "SPEC-06 §4–5", "SPEC-01 §3"], ms=["M02"]),
            dict(id=1202, title="Read PDF and Word documents with their structure", user="staff member",
                 want="answers to point at the exact section and page",
                 so="I can check the policy myself",
                 details=["Handbooks have numbered sections (e.g. §4.2) and tables."],
                 ac=["Headings, section numbers, page numbers and tables are kept.",
                     "An answer from the HR Handbook can cite something like \"HR Handbook 2026, §4.2, p.2\".",
                     "A long section is not cut in the middle of a sentence or table row."],
                 priority=1, points=8, tags="mvp", questions=[],
                 trace=["SPEC-03 §4, §5.1"], ms=["M02"]),
            dict(id=1203, title="Read Excel spreadsheets correctly", user="staff member",
                 want="to ask questions that need a lookup in a spreadsheet",
                 so="I don't have to open the file and find the row myself",
                 details=["Example: Leave_Entitlement_by_Grade_2026.xlsx — \"How many days of annual leave does a Grade M2 manager with 6 years of service get?\" → 22."],
                 ac=["Each row is understood together with its column headers.",
                     "Cells with formulas use the calculated value.",
                     "All sheets in the workbook are read."],
                 priority=1, points=5, tags="mvp",
                 questions=["Do we need to handle very large spreadsheets (thousands of rows)?"],
                 trace=["SPEC-03 §5.2"], ms=["M02"]),
            dict(id=1204, title="Read scanned documents and images", user="staff member",
                 want="scanned memos to count as much as typed documents",
                 so="I get the latest rule even when it was only sent as a scan",
                 details=["Example: the scanned HR memo of Sept 2026 raises the leave limit per application from 7 to 10 days."],
                 ac=["Text in a scanned PNG/JPG is read and can be found by questions.",
                     "If no text can be read at all, the document shows Failed with a clear reason."],
                 priority=1, points=5, tags="mvp", questions=["What about diagrams like the org chart? (see 1205)"],
                 trace=["SPEC-03 §4"], ms=["M02"]),
            dict(id=1205, title="Understand diagrams such as org charts", user="staff member",
                 want="to ask who reports to whom",
                 so="I can find the right person without the org chart open",
                 details=["Example: Org_Chart_2026.jpg."],
                 ac=["Reporting lines and job titles in the org chart can be found by questions.",
                     "Answers cite the org chart."],
                 priority=3, points=5, tags="stretch", questions=[],
                 trace=["SPEC-03 §8"], ms=["M07"]),
            dict(id=1206, title="Detect old versions automatically", user="document owner",
                 want="documents marked SUPERSEDED to be treated as old versions without my help",
                 so="nobody gets an answer from an outdated policy by mistake",
                 details=["The 2024 handbook says SUPERSEDED on page 1."],
                 ac=["A document with SUPERSEDED (or DIGANTIKAN) on its first page is marked as an old version after processing.",
                     "I can still change it by hand."],
                 priority=1, points=2, tags="mvp", questions=[],
                 trace=["SPEC-03 §6.1"], ms=["M02"]),
            dict(id=1207, title="Fill in document details automatically", user="document owner",
                 want="title, effective date, version and department filled in from the file",
                 so="I don't have to type them for every upload",
                 details=["A short summary and topic tags per document would be nice to have."],
                 ac=["When I don't give details, they are taken from the file where possible.",
                     "Details I typed myself always win.",
                     "(Nice to have) Each document gets a short summary and up to 5 tags."],
                 priority=2, points=3, tags="mvp; stretch",
                 questions=[], trace=["SPEC-03 §6, §8"], ms=["M02", "M07"]),
            dict(id=1208, title="Replace a document with a new version of the file", user="document owner",
                 want="to upload a newer file for an existing document",
                 so="links and settings stay the same",
                 details=[],
                 ac=["The document keeps its details and who-can-see settings.",
                     "Only the new content is used in answers once processing is done."],
                 priority=3, points=3, tags="stretch", questions=[],
                 trace=["SPEC-03 §7"], ms=["M08"]),
        ],
    },
    {
        "id": 1300, "slug": "ask-questions", "title": "Ask questions",
        "summary": "Staff ask questions in a chat and get short, sourced answers they can trust.",
        "stories": [
            dict(id=1301, title="Ask a question and see the answer appear as it is written", user="staff member",
                 want="to type a question and see the answer appear quickly",
                 so="it feels like talking to a colleague, not waiting for a report",
                 details=["Empty page shows a few example questions."],
                 ac=["The answer starts appearing within about 3 seconds.",
                     "Enter sends, Shift+Enter adds a new line.",
                     "I can stop an answer while it is being written.",
                     "\"New chat\" clears the conversation."],
                 priority=1, points=5, tags="mvp", questions=[],
                 trace=["SPEC-05 §1, §6", "SPEC-07 §5.1–5.2, §5.6", "SPEC-00 §7"], ms=["M04", "M05"]),
            dict(id=1302, title="See where each answer comes from", user="staff member",
                 want="every fact in an answer to show its source, and to open that source",
                 so="I can trust the answer and read the full rule",
                 details=[],
                 ac=["Every fact has a numbered reference like [1].",
                     "Under the answer I see the sources used: document, section, page and effective date.",
                     "Clicking a reference opens the document at that page (PDF), the image, or the extracted text.",
                     "An answer without any source is never shown."],
                 priority=1, points=5, tags="mvp", questions=[],
                 trace=["SPEC-05 §4", "SPEC-07 §5.3–5.4"], ms=["M04", "M05"]),
            dict(id=1303, title="Say so when the answer isn't in the documents", user="staff member",
                 want="the assistant to tell me when it doesn't know, and who to ask",
                 so="I never act on a guess",
                 details=["Examples: \"What is the ESOS vesting schedule?\", \"Can I bring my pet to the office?\" — not in any document."],
                 ac=["When no document answers the question, I see \"I couldn't find this…\" with a contact (HR, Finance or IT).",
                     "The assistant never makes up an answer."],
                 priority=1, points=3, tags="mvp",
                 questions=["Who is the right contact for each topic?"],
                 trace=["SPEC-05 §5", "SPEC-04 §4"], ms=["M03", "M04"]),
            dict(id=1304, title="Use the latest rule when documents disagree", user="staff member",
                 want="answers to follow the newest rule",
                 so="I don't apply a policy that has been changed",
                 details=["The 2024 handbook says 5 days per leave application, the 2026 handbook says 7, and the Sept 2026 memo says 10."],
                 ac=["Old versions are never used.",
                     "When a newer memo changes a handbook rule, the answer uses the memo and says it replaces the handbook."],
                 priority=1, points=3, tags="mvp", questions=[],
                 trace=["SPEC-04 §1", "SPEC-05 §2"], ms=["M03", "M04"]),
            dict(id=1305, title="Ask in Bahasa Malaysia", user="staff member",
                 want="to ask in Bahasa Malaysia and get the answer in Bahasa Malaysia",
                 so="I can use the language I'm comfortable with",
                 details=["The year-end closure notice is bilingual."],
                 ac=["A question in Malay gets an answer in Malay, with sources.",
                     "Malay and English documents are both found, whatever the language of the question."],
                 priority=2, points=2, tags="mvp", questions=[],
                 trace=["SPEC-05 §2, §5", "SPEC-03 §6", "SPEC-02 §3"], ms=["M02", "M04"]),
            dict(id=1306, title="Ask follow-up questions", user="staff member",
                 want="to ask a follow-up like \"and for managers?\"",
                 so="I don't have to repeat the whole question",
                 details=[],
                 ac=["The assistant understands a short follow-up in the same conversation.",
                     "Follow-up answers still cite documents, not earlier answers."],
                 priority=3, points=2, tags="mvp", questions=["How far back should it remember?"],
                 trace=["SPEC-05 §1", "SPEC-07 §5.6"], ms=["M04", "M05"]),
            dict(id=1307, title="Clear messages when the AI service has a problem", user="staff member",
                 want="to understand what went wrong when I can't get an answer",
                 so="I know whether to try again or tell someone",
                 details=[],
                 ac=["If the quota is used up, I'm told to contact the admin, with no Retry button.",
                     "If the service is busy or unavailable, I'm told to try again, with a Retry button.",
                     "If the connection drops mid-answer, the partial answer stays and is marked as cut off."],
                 priority=2, points=2, tags="mvp", questions=[],
                 trace=["SPEC-06 §5", "SPEC-07 §5.5"], ms=["M04", "M05"]),
        ],
    },
    {
        "id": 1400, "slug": "access-and-security", "title": "Access and security",
        "summary": "People only ever see documents they are allowed to see, and the system is safe to run.",
        "stories": [
            dict(id=1401, title="Restrict documents to groups", user="document owner",
                 want="to choose which groups can see a document",
                 so="sensitive documents (e.g. salary bands) stay with HR",
                 details=["Until we have company sign-in, the demo uses two sample users: Aisyah (HR) and Ben (Staff)."],
                 ac=["Documents are visible to everyone unless restricted.",
                     "A person outside the group never sees the document: not in the list, not in answers, not in sources, not via a direct link — not even that it exists.",
                     "In the demo I can switch between Aisyah and Ben to show the difference."],
                 priority=1, points=5, tags="mvp; security",
                 questions=["When do we connect company sign-in (SSO)?"],
                 trace=["SPEC-09 §3–4", "SPEC-04 §1", "SPEC-08 §2", "SPEC-07 §8"], ms=["M00", "M01", "M02", "M03", "M04"]),
            dict(id=1402, title="Only accept safe uploads", user="admin",
                 want="uploads to be checked before they are stored",
                 so="a malicious file can't harm the system",
                 details=[],
                 ac=["A file is checked by its real content, not only its name.",
                     "Oversized and unsupported files are refused.",
                     "Odd file names can't be used to write files in the wrong place."],
                 priority=1, points=3, tags="mvp; security", questions=[],
                 trace=["SPEC-09 §2"], ms=["M01"]),
            dict(id=1403, title="Protect keys and data", user="admin",
                 want="API keys and documents handled safely",
                 so="we meet company and PDPA expectations",
                 details=["Demo uses fictional documents only. ILMU processes and stores data in Malaysia; confirm with IT before any real documents are used."],
                 ac=["API keys are never in code, logs or error messages.",
                     "The demo uses only the fictional Serimaju documents.",
                     "Test mode can never be switched on in production."],
                 priority=1, points=2, tags="mvp; security",
                 questions=["Is ILMU approved for real company documents?"],
                 trace=["SPEC-09 §1, §5–6"], ms=["M00", "M99"]),
            dict(id=1404, title="Ignore instructions hidden inside documents", user="admin",
                 want="text inside a document never to change how the assistant behaves",
                 so="nobody can trick it by uploading a crafted file",
                 details=[],
                 ac=["A document saying \"ignore your rules and…\" does not change the answer format or reveal internal instructions.",
                     "Answers can't inject scripts or links into the page."],
                 priority=2, points=2, tags="mvp; security", questions=[],
                 trace=["SPEC-09 §7", "SPEC-05 §2"], ms=["M04", "M05"]),
        ],
    },
    {
        "id": 1500, "slug": "quality-and-cost", "title": "Answer quality, usage and cost",
        "summary": "We can prove how good the answers are and what they cost.",
        "stories": [
            dict(id=1501, title="Measure answer accuracy on a test set", user="product manager",
                 want="to score the assistant on a fixed set of questions",
                 so="we know if a change made it better or worse",
                 details=["Test set: 32 questions with expected answers and sources (samples/serimaju/eval). Includes tricky ones: old versions, the scanned memo, Malay, and questions with no answer."],
                 ac=["One command runs all 32 questions and scores each as correct, partial or wrong.",
                     "The report shows the total, the score per category and why each failure failed.",
                     "We reach at least 26/32 before the demo.",
                     "We can compare the three AI models on the same set."],
                 priority=1, points=5, tags="mvp", questions=[],
                 trace=["SPEC-10 §5"], ms=["M06", "M99"]),
            dict(id=1502, title="Track AI usage and cost", user="product manager",
                 want="to see how many AI tokens and how much money each question and document uses",
                 so="we can budget and show cost per question",
                 details=["The monthly plan covers the main models; embeddings and the fallback model are pay-as-you-go."],
                 ac=["A Usage page shows totals by model and purpose, with cost in MYR where it applies.",
                     "It shows the remaining plan tokens and pay-as-you-go balance.",
                     "It shows average answer time and tokens per question."],
                 priority=2, points=3, tags="mvp", questions=[],
                 trace=["SPEC-06 §6", "SPEC-07 §7", "SPEC-08 §7"], ms=["M04", "M05"]),
            dict(id=1503, title="Improve result ranking", user="product manager",
                 want="the most relevant passages ranked first",
                 so="answers improve on hard questions",
                 details=["Only keep it if the test score improves."],
                 ac=["Can be switched on and off by configuration.",
                     "Test scores with and without are compared and recorded."],
                 priority=3, points=3, tags="stretch", questions=[],
                 trace=["SPEC-04 §6"], ms=["M08"]),
        ],
    },
    {
        "id": 1600, "slug": "platform-and-operations", "title": "Platform and operations",
        "summary": "The system is easy to run, move to another AI provider, and later preview online.",
        "stories": [
            dict(id=1601, title="Run the whole system with one command", user="developer",
                 want="to start everything with one command on a clean machine",
                 so="anyone on the team can run the demo",
                 details=[],
                 ac=["One command starts the whole system; the README explains the steps.",
                     "It works on a clean machine with only the API key added."],
                 priority=1, points=3, tags="mvp", questions=[],
                 trace=["SPEC-11 §1–4"], ms=["M99"]),
            dict(id=1602, title="Switch AI provider without code changes", user="IT manager",
                 want="to move from ILMU to another provider (e.g. Azure AI Foundry) by configuration",
                 so="production isn't locked to the demo provider",
                 details=["ILMU is for the demo only. Production will likely run on Azure."],
                 ac=["Changing provider needs configuration only, plus a documented re-indexing step.",
                     "The test set must pass on the new provider before go-live."],
                 priority=2, points=3, tags="mvp", questions=["Which Azure region would we use?"],
                 trace=["SPEC-06 §1, §7"], ms=["M00", "M99"]),
            dict(id=1603, title="Public preview over the internet", user="product manager",
                 want="invited people to try the assistant from anywhere",
                 so="we can collect feedback after the demo",
                 details=["After the 26 Nov presentation. Still fictional documents only. Planned with Cloudflare Tunnel."],
                 ac=["Only invited emails can sign in.",
                     "Only admins can upload or change documents.",
                     "Each person has a daily question limit so the AI budget is protected.",
                     "No ports are opened on the office/home network."],
                 priority=3, points=8, tags="post-demo; security", questions=[],
                 trace=["SPEC-11 §5"], ms=["M100"]),
        ],
    },
]

# ---- Markdown per feature --------------------------------------------------
SPEC_FILES = {f"SPEC-{n:02d}": name for n, name in [
    (0, "overview"), (1, "architecture"), (2, "database-schema"), (3, "ingestion"), (4, "retrieval"),
    (5, "answering"), (6, "ai-providers"), (7, "frontend"), (8, "api-contract"), (9, "security-and-access"),
    (10, "testing-and-eval"), (11, "deployment")]}
MS_FILES = {p.stem.split("-")[0]: p.name for p in (OUT.parent / "milestones").glob("M*.md")}


def spec_link(ref: str, depth: str) -> str:
    key = ref.split(" ")[0]
    return f"[{ref}]({depth}specs/{key}-{SPEC_FILES[key]}.md)"


def ms_link(m: str, depth: str) -> str:
    return f"[{m}]({depth}milestones/{MS_FILES[m]})" if m in MS_FILES else m


def iteration(s: dict) -> str:
    return LATER if "post-demo" in s["tags"] else SPRINT


feat_dir = OUT / "features"
feat_dir.mkdir(parents=True, exist_ok=True)
for f in FEATURES:
    pts = sum(s["points"] for s in f["stories"])
    lines = [f"# Feature {f['id']} — {f['title']}", "",
             f"> **Mock Azure DevOps export.** Parent: Epic {EPIC['id']} — {EPIC['title']} · Created by {PM} · State: New · {len(f['stories'])} stories, {pts} points", "",
             f["summary"], ""]
    for s in f["stories"]:
        lines += [f"## User Story {s['id']} — {s['title']}", "",
                  f"| Priority | Story points | Iteration | Tags |", "|---|---|---|---|",
                  f"| {s['priority']} | {s['points']} | {iteration(s)} | {s['tags']} |", "",
                  f"**As a** {s['user']}, **I want** {s['want']}, **so that** {s['so']}.", ""]
        if s["details"]:
            lines += ["**Details**", ""] + [f"- {d}" for d in s["details"]] + [""]
        lines += ["**Acceptance criteria**", ""] + [f"{i}. {a}" for i, a in enumerate(s["ac"], 1)] + [""]
        if s["questions"]:
            lines += ["**Questions for the developers**", ""] + [f"- {q}" for q in s["questions"]] + [""]
    (feat_dir / f"F{f['id']}-{f['slug']}.md").write_text("\n".join(lines), encoding="utf-8")

# ---- Epic file ---------------------------------------------------------------
ep = [f"# Epic {EPIC['id']} — {EPIC['title']}", "", f"> **Mock Azure DevOps export.** Created by {PM} · State: New", ""]
ep += EPIC["description"] + ["", "**Goals**", ""] + [f"- {g}" for g in EPIC["goals"]] + ["", "**Features**", ""]
for f in FEATURES:
    ep.append(f"- [Feature {f['id']} — {f['title']}](features/F{f['id']}-{f['slug']}.md): {f['summary']}")
(OUT / f"E{EPIC['id']}-company-docs-assistant.md").write_text("\n".join(ep) + "\n", encoding="utf-8")

# ---- Traceability ------------------------------------------------------------
tr = ["# Traceability — ADO stories → specs → milestones", "",
      "Which spec sections implement each story, and which milestones build it. Keep this in step when a spec or milestone changes; reference the story in commits and PRs (`AB#1101` from GitHub, `#1101` in Azure Repos) so ADO links the work.", "",
      "| Story | Title | Spec sections | Milestones |", "|---|---|---|---|"]
for f in FEATURES:
    tr.append(f"| **F{f['id']}** | **{f['title']}** | | |")
    for s in f["stories"]:
        specs = " · ".join(spec_link(r, "../") for r in s["trace"])
        mss = ", ".join(ms_link(m, "../") for m in s["ms"])
        tr.append(f"| {s['id']} | {s['title']} | {specs} | {mss} |")
(OUT / "TRACEABILITY.md").write_text("\n".join(tr) + "\n", encoding="utf-8")

# ---- CSV import (Agile process, hierarchy via Title 1/2/3) -------------------
def h(paragraphs: list[str]) -> str:
    return "".join(f"<p>{html.escape(p).replace('**', '')}</p>" for p in paragraphs)


def ul(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{html.escape(i)}</li>" for i in items) + "</ul>" if items else ""


rows = [["ID", "Work Item Type", "Title 1", "Title 2", "Title 3", "State", "Priority", "Story Points",
         "Tags", "Description", "Acceptance Criteria"]]
rows.append(["", "Epic", EPIC["title"], "", "", "New", "1", "", "rag",
             h(EPIC["description"]) + "<p>Goals:</p>" + ul(EPIC["goals"]), ""])
for f in FEATURES:
    rows.append(["", "Feature", "", f["title"], "", "New", "1", "", "rag", h([f["summary"]]), ""])
    for s in f["stories"]:
        desc = h([f"As a {s['user']}, I want {s['want']}, so that {s['so']}."]) + ul(s["details"])
        if s["questions"]:
            desc += "<p>Questions for the developers:</p>" + ul(s["questions"])
        rows.append(["", "User Story", "", "", s["title"], "New", str(s["priority"]), str(s["points"]),
                     "rag; " + s["tags"], desc, "<ol>" + "".join(f"<li>{html.escape(a)}</li>" for a in s["ac"]) + "</ol>"])
with open(OUT / "ado-import.csv", "w", newline="", encoding="utf-8-sig") as fh:
    csv.writer(fh).writerows(rows)

n = sum(len(f["stories"]) for f in FEATURES)
print(f"features={len(FEATURES)} stories={n} points={sum(s['points'] for f in FEATURES for s in f['stories'])}")
