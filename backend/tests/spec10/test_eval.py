"""SPEC-10 §6 checks 2-3: the eval script's reports, and the source check."""

import json
from pathlib import Path

import httpx
import pytest

from app.config import get_settings
from app.eval.judge import expected_stems, final_verdict, parse_verdict, source_check
from app.eval.run import run
from tests.corpus import Corpus

HANDBOOK = "HR_Employee_Handbook_2026.pdf"


@pytest.fixture(autouse=True)
def open_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "min_vector_sim", 0.0)


async def test_spec10_ac02_eval_writes_both_reports(
    client: httpx.AsyncClient, corpus: Corpus, tmp_path: Path
) -> None:
    await corpus.add("Leave policy", ["Annual leave is fourteen days per year for confirmed staff."])

    paths = await run(client, "ben", "fake-test", {"Q01", "Q30"}, tmp_path)

    assert {p.suffix for p in paths} == {".json", ".md"}
    data = json.loads(next(p for p in paths if p.suffix == ".json").read_text(encoding="utf-8"))
    assert [r["id"] for r in data["rows"]] == ["Q01", "Q30"]
    assert data["summary"]["total"] == 2
    assert {"byCategory", "latencyP50Ms", "latencyP95Ms", "firstTokenP50Ms"} <= data["summary"].keys()
    assert all(r["verdict"] in ("correct", "partial", "wrong") for r in data["rows"])
    md = next(p for p in paths if p.suffix == ".md").read_text(encoding="utf-8")
    assert "Score:" in md and "/ 2" in md
    assert "## By category" in md and "## Failures and triage" in md
    assert "Q01" in md and "Q30" in md


def test_spec10_ac03_correct_without_expected_source_is_downgraded() -> None:
    ok = source_check("HR_Employee_Handbook_2026.pdf §4.2", ["Other.pdf"], found=True)
    assert not ok
    assert final_verdict("correct", ok) == "partial"
    assert final_verdict("wrong", ok) == "wrong"
    assert final_verdict("correct", True) == "correct"


def test_spec10_ac03_not_found_passes_only_when_found_is_false() -> None:
    assert source_check("(none)", [], found=False)
    assert not source_check("(none)", ["HR_Employee_Handbook_2026.pdf"], found=True)


def test_source_check_matches_stems_and_shorthands() -> None:
    assert expected_stems("Memo scan; HR_Employee_Handbook_2026.pdf §4.3") == [
        "memo",
        "hr_employee_handbook_2026",
    ]
    assert source_check("Memo scan", ["Memo_HR_2026-09_Leave_Policy_Amendment_scan.png"], found=True)
    assert source_check(
        "Leave_Entitlement_by_Grade_2026.xlsx (Annual Leave 2026)",
        ["leave_entitlement_by_grade_2026.XLSX"],
        found=True,
    )
    assert not source_check("Org_Chart_2026.jpg", ["HR_Employee_Handbook_2026.pdf"], found=True)


def test_parse_verdict_tolerates_wrapping_and_rejects_junk() -> None:
    assert parse_verdict('```json\n{"verdict": "Partial", "reason": "x"}\n```') == ("partial", "x")
    verdict, reason = parse_verdict("no json here")
    assert verdict == "wrong" and "unreadable" in reason
    assert parse_verdict('{"verdict": "great"}')[0] == "wrong"
