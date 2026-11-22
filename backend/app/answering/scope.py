"""The scope reply (SPEC-05 §5.1): a friendlier answer than "contact HR" when nothing was retrieved for a
question about the assistant itself or small talk ("what can you do?", "hi", "thanks").

Fixed patterns, no model call. Used only after retrieval came back empty, so a real question that happens
to match ("can you tell me the leave policy?") still gets its documents first.
"""

import re
from typing import Literal

SCOPE_TEMPLATE = (
    "I'm the {org} documents assistant. I can only answer questions from the company documents, such as "
    "leave, claims, travel or IT policies, and I show the source for every answer. "
    'Try asking something like "How many days of annual leave do I get?"'
)
SCOPE_TEMPLATE_MS = (
    "Saya pembantu dokumen {org}. Saya hanya boleh menjawab soalan berdasarkan dokumen syarikat, seperti "
    "polisi cuti, tuntutan, perjalanan atau IT, dan saya tunjukkan sumber bagi setiap jawapan. "
    'Cuba tanya, contohnya: "Berapa hari cuti tahunan saya?"'
)

_PATTERNS = [
    # About the assistant: who/what it is, what it can do, what may be asked.
    r"\bwho (are|r) (you|u)\b",
    r"\bwhat (are|r) (you|u)\b",
    r"\bwhat (can|could|do) (you|u) (do|answer|help)",
    r"\bhow (can|could|do) (you|u) help\b",
    r"\bhow do (you|u) work\b",
    r"\bcan i ask (you )?(anything|everything|something|other|about)\b",
    r"\bwhat (can|should|may) i ask\b",
    r"\b(are|r) (you|u) (a |an )?(bot|robot|human|ai|chatgpt|gpt)\b",
    r"^\s*(help|menu|start)\s*[?!.]*\s*$",
    # Small talk on its own.
    r"^\s*(hi|hello|hey|hai|helo|good (morning|afternoon|evening)|thanks?|thank you|thx|ok(ay)?)\b[\s!.?,]*"
    r"(there|again|so much|a lot)?[\s!.?]*$",
]
_PATTERNS_MS = [
    r"\bsiapa (awak|anda|kamu)\b",
    r"\b(awak|anda|kamu) (boleh|dapat) (buat|bantu|jawab) apa\b",
    r"\bapa (yang )?(awak|anda|kamu) boleh\b",
    r"\bboleh (saya|aku) tanya (apa[- ]apa|apa sahaja|soalan lain)\b",
    r"^\s*(terima kasih|selamat (pagi|petang|malam)|assalamualaikum)\b[\s!.?]*$",
]
_EN = re.compile("|".join(f"(?:{p})" for p in _PATTERNS), re.IGNORECASE)
_MS = re.compile("|".join(f"(?:{p})" for p in _PATTERNS_MS), re.IGNORECASE)


def about_assistant(question: str) -> Literal["en", "ms"] | None:
    """The language of the matched pattern, or None when the question is not about the assistant."""
    text = " ".join(question.split())
    if _MS.search(text):
        return "ms"
    return "en" if _EN.search(text) else None


def scope_text(malay: bool, org_name: str) -> str:
    return (SCOPE_TEMPLATE_MS if malay else SCOPE_TEMPLATE).format(org=org_name)
