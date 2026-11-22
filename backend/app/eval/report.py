"""Eval report (SPEC-10 §5 step 5): a JSON file with every row and a Markdown summary."""

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from app.providers.pricing import cost_myr

Row = dict[str, Any]


def percentile(values: list[int], pct: float) -> int | None:
    """Nearest-rank percentile; None for an empty list."""
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(pct / 100 * len(ordered)) - 1)]


def triage_hint(row: Row) -> str:
    """A first guess at the failing stage (parsing, chunking, retrieval, answering), to confirm by hand."""
    if row.get("error"):
        return "answering (stream error)"
    if not row["expected_sources"].strip().lower().startswith("(none)") and row.get("found") is False:
        return "retrieval (gate or ranking) or answering (refused)"
    if not row["sources_ok"]:
        return "retrieval (expected source not cited)"
    return "answering (right source, wrong or incomplete answer)"


def row_cost(meta: dict[str, Any], row: Row) -> float | None:
    if not row.get("model"):
        return 0.0  # the gate refused or the request failed before an answer call: nothing billed
    cost = cost_myr(meta["provider"], row["model"], row["prompt_tokens"], row["completion_tokens"])
    return float(cost) if cost is not None else None


def summarize(meta: dict[str, Any], rows: list[Row]) -> dict[str, Any]:
    by_category: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        by_category[r["category"]].append(r["score"])
    latencies = [r["latency_ms"] for r in rows if r["latency_ms"] is not None]
    first = [r["first_token_ms"] for r in rows if r["first_token_ms"] is not None]
    costs = [row_cost(meta, r) for r in rows]
    return {
        "score": sum(r["score"] for r in rows),
        "total": len(rows),
        "counts": {v: sum(1 for r in rows if r["verdict"] == v) for v in ("correct", "partial", "wrong")},
        "byCategory": {
            c: {"score": sum(s), "total": len(s), "percent": round(100 * sum(s) / len(s))}
            for c, s in sorted(by_category.items())
        },
        "latencyP50Ms": percentile(latencies, 50),
        "latencyP95Ms": percentile(latencies, 95),
        "firstTokenP50Ms": percentile(first, 50),
        "promptTokensPerQuestion": round(sum(r["prompt_tokens"] for r in rows) / len(rows)),
        "completionTokensPerQuestion": round(sum(r["completion_tokens"] for r in rows) / len(rows)),
        "costMyrPerQuestion": (
            round(sum(c for c in costs if c is not None) / len(rows), 6)
            if all(c is not None for c in costs)
            else None
        ),
    }


def cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def render_markdown(meta: dict[str, Any], rows: list[Row], summary: dict[str, Any]) -> str:
    pct = round(100 * summary["score"] / summary["total"])
    counts = summary["counts"]
    cost = summary["costMyrPerQuestion"]
    lines = [
        f"# Eval {meta['label']} — {meta['date']}",
        "",
        f"- **Score: {summary['score']:g} / {summary['total']} ({pct}%)** — "
        f"{counts['correct']} correct, {counts['partial']} partial, {counts['wrong']} wrong",
        f"- Answer model `{meta['answerModel']}`, judge `{meta['judgeModel']}`, "
        f"provider `{meta['provider']}`, user `{meta['user']}`",
        f"- Latency p50 {summary['latencyP50Ms']} ms, p95 {summary['latencyP95Ms']} ms; "
        f"first token p50 {summary['firstTokenP50Ms']} ms",
        f"- Tokens per question: {summary['promptTokensPerQuestion']} in, "
        f"{summary['completionTokensPerQuestion']} out; cost per question: "
        + (f"MYR {cost:.4f}" if cost is not None else "n/a (plan-quota model)"),
        "",
        "## By category",
        "",
        "| Category | Score | % |",
        "|---|---|---|",
    ]
    for category, c in summary["byCategory"].items():
        lines.append(f"| {cell(category)} | {c['score']:g} / {c['total']} | {c['percent']}% |")
    lines += [
        "",
        "## All questions",
        "",
        "| Id | Verdict | Found | Sources | Latency | Reason |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        mark = "ok" if r["sources_ok"] else "miss"
        verdict = r["verdict"] + (" (downgraded)" if r["verdict"] != r["judge_verdict"] else "")
        lines.append(
            f"| {r['id']} | {verdict} | {r['found']} | {mark} | {r['latency_ms']} ms "
            f"| {cell(r['judge_reason'])} |"
        )
    failures = [r for r in rows if r["verdict"] != "correct"]
    lines += ["", "## Failures and triage", ""]
    if not failures:
        lines.append("None.")
    else:
        lines += [
            "Cause hint is automatic; confirm by hand as parsing, chunking, retrieval or answering.",
            "",
            "| Id | Verdict | Question | Expected | Got | Cited | Reason | Cause hint |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for r in failures:
            lines.append(
                f"| {r['id']} | {r['verdict']} | {cell(r['question'])} | {cell(r['expected_answer'])} "
                f"| {cell(r['answer'])[:300]} | {cell(', '.join(r['cited']) or '-')} "
                f"| {cell(r['judge_reason'])} | {triage_hint(r)} |"
            )
    return "\n".join(lines) + "\n"


def write_reports(out_dir: Path, meta: dict[str, Any], rows: list[Row]) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize(meta, rows)
    stem = f"{meta['date']}-{meta['label']}"
    json_path, md_path = out_dir / f"{stem}.json", out_dir / f"{stem}.md"
    json_path.write_text(
        json.dumps({"meta": meta, "summary": summary, "rows": rows}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(render_markdown(meta, rows, summary), encoding="utf-8")
    return [json_path, md_path]
