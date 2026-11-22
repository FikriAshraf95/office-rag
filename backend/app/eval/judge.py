"""LLM judge for the evaluation (SPEC-10 §5 step 3). Goes through `providers`, `purpose = 'eval'`."""

import json
import re
from dataclasses import dataclass
from typing import Literal

from app.providers.base import ChatModel, Message, TokenUsage

Verdict = Literal["correct", "partial", "wrong"]
VERDICTS: tuple[Verdict, ...] = ("correct", "partial", "wrong")
SCORES: dict[str, float] = {"correct": 1.0, "partial": 0.5, "wrong": 0.0}

SYSTEM_PROMPT = """You grade answers from a company-documents assistant against a reference answer.

Return only JSON: {"verdict": "correct" | "partial" | "wrong", "reason": "<one short sentence>"}

- correct: the answer states the right facts from the current version of the policy and keeps the conditions.
- partial: the core fact is right, but a condition is missing or the wording is weak or vague.
- wrong: a wrong or outdated value, a contradiction of the reference, or a guess where the reference says the
  documents do not contain the answer.
When the reference says the information is not in the documents, an answer that says it could not find it
is correct, and an answer that invents a value is wrong. Ignore citation markers like [1] and formatting.
The notes describe traps (for example an outdated document); an answer that falls into the trap is wrong."""

_JSON_OBJECT = re.compile(r"\{.*\}", re.DOTALL)


@dataclass(slots=True)
class Judgement:
    verdict: Verdict
    reason: str
    usage: TokenUsage


def build_messages(question: str, expected: str, notes: str, answer: str) -> list[Message]:
    user = (
        f"Question: {question}\n\nReference answer: {expected}\n\nNotes: {notes or '(none)'}\n\n"
        f"System answer:\n{answer.strip() or '(empty)'}"
    )
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}]


def parse_verdict(text: str) -> tuple[Verdict, str]:
    """A verdict from the judge's reply; anything unreadable is `wrong` with the reason saying so."""
    match = _JSON_OBJECT.search(text)
    try:
        data = json.loads(match.group(0)) if match else None
    except json.JSONDecodeError:
        data = None
    if isinstance(data, dict):
        verdict = str(data.get("verdict", "")).strip().lower()
        if verdict in VERDICTS:
            return verdict, str(data.get("reason", ""))
    return "wrong", f"judge reply unreadable: {text[:120]!r}"


async def judge(
    model: ChatModel, *, question_id: str, question: str, expected: str, notes: str, answer: str
) -> Judgement:
    result = await model.complete(
        build_messages(question, expected, notes, answer),
        json_mode=True,
        reasoning="low",
        purpose="eval",
        ref_id=question_id,
    )
    verdict, reason = parse_verdict(result.text)
    return Judgement(verdict, reason, result.usage)


def expected_stems(expected_sources: str) -> list[str]:
    """`HR_Handbook_2026.pdf §4.2; Memo scan` -> [`hr_handbook_2026`, `memo`].

    The CSV uses shorthands ("Memo scan", "Client_Engagement policy"), so the first whitespace-delimited
    word of each `;` entry, minus its extension, is matched as a filename-stem prefix. `(none)` means a
    not-found question and yields [].
    """
    stems: list[str] = []
    for part in expected_sources.split(";"):
        part = part.strip()
        if not part or part.lower() == "(none)":
            continue
        word = part.split()[0].lower()
        stems.append(word.rsplit(".", 1)[0] if re.search(r"\.[a-z]{2,4}$", word) else word)
    return stems


def source_check(expected_sources: str, cited_filenames: list[str], found: bool) -> bool:
    """True when a cited document matches an expected source; not-found questions pass on `found = false`."""
    stems = expected_stems(expected_sources)
    if not stems:
        return not found
    cited = [name.lower() for name in cited_filenames]
    return any(name.startswith(stem) for stem in stems for name in cited)


def final_verdict(verdict: Verdict, sources_ok: bool) -> Verdict:
    """A `correct` verdict whose citations miss every expected source is downgraded to `partial`."""
    return "partial" if verdict == "correct" and not sources_ok else verdict
