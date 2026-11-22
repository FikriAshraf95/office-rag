"""`python -m app.export_openapi` writes backend/openapi.json for the frontend types."""

import json
from pathlib import Path
from typing import Any

from pydantic.json_schema import models_json_schema

from app.api.schemas import SseDelta, SseDone, SseError, SseMeta, SseSources
from app.main import create_app

OUT = Path(__file__).resolve().parent.parent / "openapi.json"
SSE_MODELS = (SseMeta, SseSources, SseDelta, SseDone, SseError)


def build() -> dict[str, Any]:
    """The app's OpenAPI document plus the SSE event schemas (SPEC-08 §6), which FastAPI can't describe."""
    document = create_app(guards=False).openapi()
    _, sse = models_json_schema(
        [(m, "serialization") for m in SSE_MODELS], ref_template="#/components/schemas/{model}"
    )
    document.setdefault("components", {}).setdefault("schemas", {}).update(sse.get("$defs", {}))
    return document


def main() -> None:
    OUT.write_text(json.dumps(build(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
