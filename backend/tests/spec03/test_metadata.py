"""SPEC-03 §6 metadata rules and §5.2 sheet chunking, without Docling or a database."""

from datetime import date
from pathlib import Path

from app.config import get_settings
from app.ingestion import metadata
from app.ingestion.chunking import WhitespaceCounter, chunk_sheets
from app.ingestion.extract import DocInfo, extract
from app.ingestion.parsers.xlsx import Sheet

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "serimaju"


def test_spec03_ac12_front_matter_fills_title_version_date_and_department() -> None:
    front, body = metadata.split_front_matter((FIXTURES / "Travel_and_Claims_SOP.md").read_text("utf-8"))
    assert front["title"] == "Travel and Claims SOP"
    assert str(front["version"]) == "2.3"
    assert metadata.parse_date(front["effective"]) == date(2026, 2, 1)
    assert metadata.department_from_owner(front["owner"]) == "Finance"
    assert body.startswith("# Travel and Claims SOP")


def test_spec03_front_matter_valid_yaml_dates_and_numbers() -> None:
    front, _ = metadata.split_front_matter("---\ntitle: T\nversion: 2.3\neffective: 2026-02-01\n---\nbody")
    assert front == {"title": "T", "version": 2.3, "effective": date(2026, 2, 1)}
    assert metadata.parse_date(front["effective"]) == date(2026, 2, 1)


def test_spec03_front_matter_is_never_executed() -> None:
    front, _ = metadata.split_front_matter("---\nx: !!python/object/apply:os.system ['echo hi']\n---\nbody")
    assert "x" not in front or isinstance(front["x"], str)


def test_spec03_superseded_needs_the_whole_word_in_the_first_2000_chars() -> None:
    assert metadata.is_superseded("Handbook\nSUPERSEDED: replaced by 2026")
    assert metadata.is_superseded("DIGANTIKAN oleh versi baharu")
    assert not metadata.is_superseded("This policy supersedes the old one")
    assert not metadata.is_superseded("NOTSUPERSEDED")
    assert not metadata.is_superseded("x" * 2100 + " SUPERSEDED")


def test_spec03_effective_date_forms() -> None:
    assert metadata.find_effective_date("Version 2 - Effective 1 January 2026") == date(2026, 1, 1)
    assert metadata.find_effective_date("Effective date: 2026-03-01") == date(2026, 3, 1)
    assert metadata.find_effective_date("Berkuat kuasa 15 Mac 2026") == date(2026, 3, 15)
    assert metadata.find_effective_date("nothing here") is None


def test_spec03_doc_type_version_and_title_from_filename() -> None:
    assert metadata.doc_type_from_filename("HR_Employee_Handbook_2026.pdf") == "handbook"
    assert metadata.doc_type_from_filename("Memo_HR_2026-09_Leave.png") == "memo"
    assert metadata.doc_type_from_filename("Travel_and_Claims_SOP.md") == "sop"
    assert metadata.doc_type_from_filename("IT_Security_Policy_v3.docx") == "policy"
    assert metadata.doc_type_from_filename("Notis_Penutupan.pdf") == "notice"
    assert metadata.doc_type_from_filename("Org_Chart_2026.jpg") == "chart"
    assert metadata.doc_type_from_filename("Client_Accounts.xlsx") == "spreadsheet"
    assert metadata.doc_type_from_filename("random.pdf") == "other"
    assert metadata.version_from_filename("IT_Security_Policy_v3.docx") == "v3"
    assert metadata.version_from_filename("Handbook_2026.pdf") is None
    assert metadata.title_from_filename("Travel_and_Claims_SOP.md") == "Travel and Claims SOP"


def test_spec03_form_title_wins_but_the_filename_default_may_be_replaced() -> None:
    assert (
        metadata.resolve_title("Travel and Claims SOP", "Travel_and_Claims_SOP.md", "Real Title")
        == "Real Title"
    )
    assert metadata.resolve_title("My title", "Travel_and_Claims_SOP.md", "Real Title") == "My title"


def test_spec03_language_thresholds() -> None:
    assert metadata.detect_language("The leave policy applies to all employees.") == "en"
    assert (
        metadata.detect_language("Kakitangan yang tidak hadir dan akan dikenakan tindakan untuk hari ini")
        == "ms"
    )
    assert metadata.detect_language("Office closes on Friday untuk semua staff and the team") == "mixed"


def test_spec03_xlsx_chunks_split_by_rows_with_header_repeated() -> None:
    sheet = Sheet(name="S", header=["Grade", "Days"], rows=[[f"G{i}", str(i)] for i in range(45)])
    chunks = chunk_sheets("Book", [sheet], WhitespaceCounter(), rows_per_chunk=20, max_tokens=800)
    assert [c.chunk_type for c in chunks] == ["table_rows"] * 3
    assert all("| Grade | Days |" in c.text for c in chunks)
    assert chunks[0].text.count("Grade: G") == 20
    assert chunks[2].text.count("Grade: G") == 5
    assert all(c.heading_path == ["Book", "S"] and c.sheet == "S" for c in chunks)


def test_spec03_xlsx_other_sheet_calculator_and_notes_become_label_value_lines() -> None:
    info = DocInfo("Leave", "Leave_Entitlement_by_Grade_2026.xlsx", "xlsx")
    result = extract(
        FIXTURES / "Leave_Entitlement_by_Grade_2026.xlsx", info, get_settings(), WhitespaceCounter()
    )
    other = next(c for c in result.chunks if c.sheet == "Other Leave" and c.chunk_type == "table_rows")
    assert "Leave type: Maternity leave; Entitlement: 98 days; Notes: Consecutive" in other.text
    assert result.meta.doc_type == "spreadsheet"
    assert result.meta.effective_date == date(2026, 1, 1)
