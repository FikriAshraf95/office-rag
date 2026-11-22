"""Shared checks used by more than one spec test."""

import re
from pathlib import Path

from app.config import Settings

APP = Path(__file__).resolve().parent.parent / "app"
PRIVATE_MARKER = "ZQX-PRIVATE-7"
SDK_IMPORT = re.compile(r"^\s*(import|from)\s+(openai|httpx2?)\b", re.MULTILINE)


def model_names() -> set[str]:
    s = Settings(_env_file=None)
    names = {
        s.llm_answer_model,
        s.llm_fast_model,
        s.llm_fallback_model,
        s.llm_vision_model,
        s.llm_judge_model,
        s.embed_model,
        "bge-reranker",
    }
    return {n for n in names if n}


def provider_leaks() -> list[str]:
    """Files outside app/providers/ (and config.py) that name a model or import a provider SDK."""
    leaks: list[str] = []
    for path in APP.rglob("*.py"):
        rel = path.relative_to(APP).as_posix()
        if rel.startswith("providers/") or rel == "config.py":
            continue
        text = path.read_text(encoding="utf-8")
        leaks += [f"{rel}: model name {name!r}" for name in model_names() if name in text]
        if SDK_IMPORT.search(text):
            leaks.append(f"{rel}: imports a provider SDK")
    return leaks
