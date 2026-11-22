"""The scope reply (SPEC-05 §5.1): a friendlier answer than "contact HR" when nothing was retrieved for a
question about the assistant itself or small talk ("what can you do?", "hi", "thanks").

Fixed patterns, no model call. Used only after retrieval came back empty, so a real question that happens
to match ("can you tell me the leave policy?") still gets its documents first.

Matching, after a leading greeting is dropped ("hi, can you ..."):
1. a direct pattern about the assistant ("who are you", "what u can do", "how to use this"), or
2. an off-topic word ("anything else", "other thing", "not about the company", "soalan lain") together with
   a "you" word or an asking verb ("u", "awak", "ask", "answer", "tanya"). Broken English and Manglish are
   expected: "u can answer other thing?", "can ask other question or not", "boleh tanya benda lain tak".
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

_YOU = r"(?:you|u|yu|ur|your|bot|chatbot|awak|anda|kamu|hang|ko|kau)"
_THING = (
    r"(?:thing|things|thng|question|questions|qn|qns|questn|qs|topic|topics|stuff|subject|subjects|"
    r"matter|matters|info|benda|soalan|hal|topik|perkara)"
)
_ANYTHING = r"(?:anything|anythin|anythng|anyting|any thing|something|somethin|smth|everything|evrything)"
_WORK = r"(?:company|companies|work|kerja|document|documents|doc|docs|serimaju|syarikat|dokumen|office stuff)"

_SMALL_TALK = (
    r"(?:hi+|hello+|hey+|hai+|helo+|yo|good (?:morning|afternoon|evening)|thanks?|thank you|thank u|thx|"
    r"tq|ty|ok(?:ay)?|okie|noted|nice|cool|great|bye)"
)

_GREETING = re.compile(
    r"^(?:hi+|hello+|hey+|hai+|helo+|yo|salam|assalamualaikum|good (?:morning|afternoon|evening))\b[\s,!.~]*",
    re.IGNORECASE,
)

# 1. About the assistant itself.
_DIRECT_EN = [
    rf"\bwho (?:are|r|is) {_YOU}\b",
    rf"\bwhat (?:are|r) {_YOU}\b",
    rf"\bwhat (?:can|could|do|does) {_YOU} (?:do|answer|help|know)",
    rf"\bwhat {_YOU} (?:can|could|do) (?:do|answer|help)",  # broken English: "what u can do"
    rf"\b{_YOU} (?:can|could) (?:do|answer|help(?: with)?) what\b",  # "u can do what"
    rf"\bhow (?:can|could|do|does|will) {_YOU} help\b",
    rf"\bhow (?:do|does) {_YOU} work\b",
    r"\bhow (?:to|do i|can i) use (?:you|u|this|dis|the) ?(?:app|bot|chat|system|assistant|thing)?\b",
    r"\bwhat (?:is|s|'s)? ?(?:this|dis) (?:app|bot|chat|system|assistant|thing)\b",
    rf"\bwhat (?:is|s|'s)? ?{_YOU} (?:job|function|purpose|use|for)\b",
    r"\bwhat (?:can|should|may|to) i ask\b",
    rf"\bcan i ask {_YOU}\b",
    rf"\b(?:are|r) {_YOU} (?:a |an )?(?:bot|robot|human|real person|ai|chatgpt|gpt)\b",
    rf"\b{_YOU} (?:know|knw) (?:everything|evrything|all|anything)\b",
    r"^\s*(?:help|menu|start|test|testing)\s*[?!.]*\s*$",
    # Small talk on its own.
    rf"^\s*{_SMALL_TALK}(?:[\s,!.~]+(?:{_SMALL_TALK}|there|again|so much|a lot|bro|sis|all))*[\s!.?~]*$",
]
_DIRECT_MS = [
    r"\bsiapa (?:awak|anda|kamu|ko|kau|hang)\b",
    r"\b(?:awak|anda|kamu|ko|kau|hang) (?:boleh|bole|leh|dapat) (?:buat|bantu|jawab|tolong) apa\b",
    r"\bapa (?:yang )?(?:awak|anda|kamu|ko|kau|hang) (?:boleh|bole|leh|tahu|buat)\b",
    r"\bmacam ?mana (?:nak )?guna\b",
    r"^\s*(?:terima kasih|tq|selamat (?:pagi|petang|malam)|assalamualaikum)\b[\s!.?]*$",
]

# 2. Off-topic words, matched only with an ability or "you" word.
_OFF_TOPIC_EN = [
    rf"\b{_ANYTHING} (?:else|other|at all|random)\b",
    rf"\bask (?:{_YOU} )?(?:about )?{_ANYTHING}\b",
    rf"\b(?:other|another|different|random|general|outside|non[- ]?work|personal) {_THING}\b",
    rf"\b(?:what|anything|something) else (?:can|could|do) {_YOU}\b",
    rf"\bask (?:{_YOU} )?(?:something |anything |sth )?else\b",
    rf"\bnot (?:about|abt|related(?: to| with)?|relate(?: to)?|regarding|on|for|from) "
    rf"(?:the |our |this |my |ur |your )?{_WORK}\b",
    rf"\b(?:outside|beside|besides|other than|apart from|except|instead of) "
    rf"(?:the |of |our |this |my )?{_WORK}(?: {_THING})?\b",
    r"\boutside (?:of )?work (?:stuff|topics?|questions?|things?)\b",
    r"\b(?:un ?related|off[- ]?topic|general knowledge)\b",
    rf"\bonly (?:can |answer |about |for |know )*(?:the |our )?{_WORK}\b",
    rf"\bnon[- ]?{_WORK}\b",
]
_OFF_TOPIC_MS = [
    rf"\b{_THING} lain\b",
    rf"\b(?:selain|kecuali|luar|luar dari|luar daripada) (?:dari |daripada )?{_WORK}\b",
    rf"\bbukan (?:pasal|psl|tentang|berkaitan|berkenaan) {_WORK}\b",
    rf"\b(?:apa[- ]apa|apa sahaja|apa saja|semua) {_THING}\b",
    r"\btanya (?:apa[- ]apa|apa sahaja|apa saja|lagi)\b",
]
# "can" alone is not enough ("Can I claim anything else?" is a policy question): a "you" word or asking.
_ABILITY = re.compile(
    rf"\b(?:{_YOU}|ask|asking|answer|answering|reply|talk|chat|discuss|tanya|jawab|sembang)\b", re.IGNORECASE
)
_MALAY_WORDS = re.compile(
    r"\b(?:boleh|bole|leh|awak|anda|kamu|tanya|soalan|benda|lain|selain|tak|ke|apa|nak|saya|aku|pasal)\b",
    re.IGNORECASE,
)


def _any(patterns: list[str]) -> re.Pattern[str]:
    return re.compile("|".join(f"(?:{p})" for p in patterns), re.IGNORECASE)


_EN_DIRECT, _MS_DIRECT = _any(_DIRECT_EN), _any(_DIRECT_MS)
_EN_OFF, _MS_OFF = _any(_OFF_TOPIC_EN), _any(_OFF_TOPIC_MS)


def about_assistant(question: str) -> Literal["en", "ms"] | None:
    """The reply language when the question is about the assistant, or None when it is not."""
    text = " ".join(question.split())
    if _MS_DIRECT.search(text) or _EN_DIRECT.search(text):
        return "ms" if _MS_DIRECT.search(text) else "en"
    rest = _GREETING.sub("", text)  # "hi, can you answer ..." is judged by what follows the greeting
    if _EN_DIRECT.search(rest):
        return "en"
    off_topic = _MS_OFF.search(rest) or _EN_OFF.search(rest)
    if off_topic and _ABILITY.search(rest):
        return "ms" if _MS_OFF.search(rest) or len(_MALAY_WORDS.findall(rest)) >= 2 else "en"
    return None


def scope_text(malay: bool, org_name: str) -> str:
    return (SCOPE_TEMPLATE_MS if malay else SCOPE_TEMPLATE).format(org=org_name)
