"""Print what retrieval returns for every eval question, to tune MIN_VECTOR_SIM (M03).

    uv run python -m app.eval.inspect_search [--user ben] [--only Q01,Q02] [--k 8]

Runs against the database in DATABASE_URL with the real providers in .env. Reads only: it never ingests
the CSV. M06 adds the scored evaluation next to this file.
"""

import argparse
import asyncio
import csv
import sys
from pathlib import Path

from sqlalchemy import select

from app.config import Settings, get_settings
from app.db.engine import get_sessionmaker
from app.db.models import Document
from app.providers.registry import get_providers
from app.retrieval.search import Hit, fetch_candidates, passes_gate, prepare_query, search
from app.security.identity import demo_identity

CSV_PATH = Path(__file__).resolve().parents[3] / "samples" / "serimaju" / "eval" / "eval_questions.csv"


def expected_prefixes(expected_sources: str) -> list[str]:
    """`File.pdf §4.2; Memo scan; Leave_Entitlement xlsx (Other Leave)` -> filename prefixes, lowercase.

    The first whitespace-delimited word of each entry is matched as a filename prefix, which covers the
    shorthands in the CSV ("Memo scan", "Client_Engagement policy").
    """
    prefixes: list[str] = []
    for part in expected_sources.split(";"):
        part = part.strip()
        if part and part.lower() != "(none)":
            prefixes.append(part.split()[0].lower())
    return prefixes


def describe(hit: Hit) -> str:
    where = hit.sheet or hit.section or "-"
    rank = f"vec#{hit.vec_rank or '-'} fts#{hit.fts_rank or '-'}"
    sim = f"{hit.vec_sim:.3f}" if hit.vec_sim is not None else "  -  "
    return f"{hit.score:.4f} {rank:<14} sim={sim}  {hit.title[:42]:<42} [{where}]"


async def run(user_id: str, only: set[str], k: int, settings: Settings) -> None:
    rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8")))
    if only:
        rows = [r for r in rows if r["id"] in only]
    user = demo_identity(user_id, settings)
    providers = get_providers()
    answerable_sims: list[tuple[str, float]] = []
    notfound_sims: list[tuple[str, float]] = []
    found = total = 0
    misses: list[str] = []
    async with get_sessionmaker()() as session:
        for row in rows:
            query = prepare_query(row["question"])
            (qvec,) = await providers.embedder().embed([query], purpose="question")
            candidates = await fetch_candidates(session, query, qvec, list(user.groups), settings)
            best = max((h.vec_sim for h in candidates if h.vec_sim is not None), default=0.0)
            gate = passes_gate(query, candidates, settings)
            hits = (await search(session, query, user, k, settings=settings, providers=providers))[:k]
            print(f"\n{row['id']} [{row['category']}] {query}")
            print(f"   best vec_sim={best:.3f} gate={'pass' if gate else 'FAIL'} hits={len(hits)}")
            for i, hit in enumerate(hits, 1):
                print(f"   {i}. {describe(hit)}")
            prefixes = expected_prefixes(row["expected_sources"])
            if not prefixes:
                notfound_sims.append((row["id"], best))
                if hits:
                    misses.append(f"{row['id']}: not-found question returned {len(hits)} hits")
                continue
            answerable_sims.append((row["id"], best))
            names = [h.filename.lower() for h in hits]
            for prefix in prefixes:
                total += 1
                if any(n.startswith(prefix) for n in names):
                    found += 1
                else:
                    misses.append(f"{row['id']}: missing {prefix}")
    print("\n=== summary ===")
    if total:
        print(f"recall@{k}: {found}/{total} = {found / total:.3f} (expected source files in the top {k})")
    print("misses:" if misses else "misses: none")
    for miss in misses:
        print(f"  {miss}")
    if answerable_sims:
        low = min(answerable_sims, key=lambda t: t[1])
        print(
            f"answerable best vec_sim: min={low[1]:.3f} ({low[0]}), "
            f"max={max(s for _, s in answerable_sims):.3f}"
        )
        print(
            "  lowest five: "
            + ", ".join(f"{q}={s:.3f}" for q, s in sorted(answerable_sims, key=lambda t: t[1])[:5])
        )
    if notfound_sims:
        print("not-found best vec_sim: " + ", ".join(f"{q}={s:.3f}" for q, s in notfound_sims))
    print(f"current MIN_VECTOR_SIM={settings.min_vector_sim}")
    # Which documents exist, so a miss can be told from a missing upload.
    async with get_sessionmaker()() as session:
        docs = (await session.execute(select(Document.filename, Document.status))).all()
    print(f"documents in database: {len(docs)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--user", default="ben")
    parser.add_argument("--only", default="", help="comma-separated question ids, e.g. Q01,Q02")
    parser.add_argument("--k", type=int, default=8)
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    only = {q.strip() for q in args.only.split(",") if q.strip()}
    asyncio.run(run(args.user, only, args.k, get_settings()))


if __name__ == "__main__":
    main()
