"""Scored evaluation on the Serimaju questions (SPEC-10 §5).

    uv run python -m app.eval --base-url http://localhost:8000 --user ben --label baseline [--only Q01,Q28]

Asks every question through `POST /api/v1/chat` like a user, judges the answers with the `judge` role and
writes `eval-results/<date>-<label>.{json,md}`. Reads the CSV only; it never ingests it. Needs DATABASE_URL
because the judge's usage is logged (`purpose = 'eval'`).
"""

import argparse
import asyncio
import csv
import json
import sys
from collections import Counter
from collections.abc import AsyncIterator
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.eval.judge import SCORES, Verdict, final_verdict, judge, source_check
from app.eval.report import write_reports
from app.providers.api_client import TRANSPORT_ERRORS, ApiClient, ApiResponse, make_api_client
from app.providers.base import ChatModel
from app.providers.registry import get_providers

REPO = Path(__file__).resolve().parents[3]
CSV_PATH = REPO / "samples" / "serimaju" / "eval" / "eval_questions.csv"
RESULTS_DIR = REPO / "eval-results"


@dataclass(slots=True)
class Row:
    id: str
    category: str
    question: str
    expected_answer: str
    expected_sources: str
    answer: str = ""
    found: bool | None = None
    cited: list[str] = field(default_factory=list)  # filenames of the cited sources
    model: str | None = None
    latency_ms: int | None = None
    first_token_ms: int | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    error: str | None = None
    judge_verdict: Verdict = "wrong"
    judge_reason: str = ""
    judge_tokens: int = 0
    sources_ok: bool = False
    verdict: Verdict = "wrong"

    @property
    def score(self) -> float:
        return SCORES[self.verdict]


@dataclass(slots=True)
class ChatOutcome:
    answer: str = ""
    sources: list[dict[str, Any]] = field(default_factory=list)
    done: dict[str, Any] | None = None
    error: str | None = None


def load_questions(path: Path = CSV_PATH, only: set[str] | None = None) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows if not only or r["id"] in only]


async def sse_events(response: ApiResponse) -> AsyncIterator[tuple[str, dict[str, Any]]]:
    name = ""
    async for line in response.aiter_lines():
        if line.startswith("event:"):
            name = line.removeprefix("event:").strip()
        elif line.startswith("data:") and name:
            yield name, json.loads(line.removeprefix("data:").strip())
            name = ""


async def ask(client: ApiClient, question: str) -> ChatOutcome:
    """Streams one answer. The final text is `done.finalText` when present, else the joined deltas."""
    out = ChatOutcome()
    deltas: list[str] = []
    try:
        async with client.stream("POST", "/api/v1/chat", json={"question": question, "history": []}) as resp:
            if resp.status_code != 200:
                body = (await resp.aread()).decode("utf-8", "replace")
                out.error = f"http {resp.status_code}: {body[:200]}"
                return out
            async for name, data in sse_events(resp):
                if name == "sources":
                    out.sources = data.get("sources", [])
                elif name == "delta":
                    deltas.append(data.get("text", ""))
                elif name == "done":
                    out.done = data
                elif name == "error":
                    out.error = f"{data.get('code')}: {data.get('detail')}"
    except TRANSPORT_ERRORS as exc:
        out.error = f"transport: {exc!r}"
    final = (out.done or {}).get("finalText")
    out.answer = final if final is not None else "".join(deltas)
    if out.done is None and out.error is None:
        out.error = "stream ended without a done event"
    return out


async def filenames_by_id(client: ApiClient) -> dict[str, str]:
    resp = await client.get("/api/v1/documents")
    resp.raise_for_status()
    return {d["id"]: d["filename"] for d in resp.json()["items"]}


async def evaluate_row(
    client: ApiClient, judge_model: ChatModel, q: dict[str, str], filenames: dict[str, str]
) -> Row:
    row = Row(
        id=q["id"],
        category=q["category"],
        question=q["question"],
        expected_answer=q["expected_answer"],
        expected_sources=q["expected_sources"],
    )
    out = await ask(client, q["question"])
    row.answer = out.answer
    row.error = out.error
    cited_numbers = set((out.done or {}).get("cited", []))
    row.cited = sorted(
        {filenames.get(s["documentId"], s["title"]) for s in out.sources if s["n"] in cited_numbers}
    )
    if out.done:
        row.found = out.done["found"]
        row.model = out.done.get("model")
        row.latency_ms = out.done["latencyMs"]
        row.first_token_ms = out.done.get("firstTokenMs")
        row.prompt_tokens = out.done["usage"]["promptTokens"]
        row.completion_tokens = out.done["usage"]["completionTokens"]
    if out.error is not None and not out.answer:
        row.judge_reason = f"no answer ({out.error})"
        return row  # verdict stays "wrong"
    verdict = await judge(
        judge_model,
        question_id=row.id,
        question=row.question,
        expected=row.expected_answer,
        notes=q.get("notes", ""),
        answer=row.answer,
    )
    row.judge_verdict, row.judge_reason = verdict.verdict, verdict.reason
    row.judge_tokens = verdict.usage.total_tokens
    row.sources_ok = source_check(row.expected_sources, row.cited, bool(row.found))
    row.verdict = final_verdict(verdict.verdict, row.sources_ok)
    return row


async def run(client: ApiClient, user: str, label: str, only: set[str], out_dir: Path) -> list[Path]:
    """Evaluates through `client` (an API client with the demo-user header); returns the report paths."""
    questions = load_questions(only=only)
    if not questions:
        raise SystemExit("no questions selected")
    judge_model = get_providers().chat("judge")
    rows: list[Row] = []
    filenames = await filenames_by_id(client)
    for q in questions:
        row = await evaluate_row(client, judge_model, q, filenames)
        rows.append(row)
        print(f"{row.id:<4} {row.verdict:<8} {row.latency_ms or '-'} ms  {row.judge_reason[:80]}", flush=True)
    settings = get_settings()
    # The API that answered may run another model than this process's settings name; trust the answers.
    answered = Counter(r.model for r in rows if r.model)
    meta = {
        "label": label,
        "date": date.today().isoformat(),
        "user": user,
        "provider": settings.ai_provider,
        "answerModel": answered.most_common(1)[0][0] if answered else settings.llm_answer_model,
        "judgeModel": judge_model.model,
        "total": len(rows),
    }
    return write_reports(out_dir, meta, [asdict(r) | {"score": r.score} for r in rows])


async def run_remote(base_url: str, user: str, label: str, only: set[str], out_dir: Path) -> list[Path]:
    async with make_api_client(base_url, user) as client:
        return await run(client, user, label, only, out_dir)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--user", default="ben")
    parser.add_argument("--label", required=True)
    parser.add_argument("--only", default="", help="comma-separated question ids, e.g. Q01,Q28")
    parser.add_argument("--out-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    only = {q.strip() for q in args.only.split(",") if q.strip()}
    for path in asyncio.run(run_remote(args.base_url, args.user, args.label, only, args.out_dir)):
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
