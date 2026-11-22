#!/usr/bin/env bash
# SPEC-11 §6 checks 1–4 against the running full stack: the live half of tests/spec11 (which checks the
# config statically). Run from the repo root after `docker compose up -d --build` and uploading the
# Serimaju documents (check 2 asks a real question):
#
#   bash scripts/release_check.sh
#
# Needs only Docker, curl and GNU date (Git Bash on Windows is fine). Prints no secret values.
set -euo pipefail
export MSYS_NO_PATHCONV=1

BASE=${BASE:-http://localhost:8080}
QUESTION=${QUESTION:-How many days of annual leave does a Grade M2 manager with 6 years of service get?}
failed=0
pass() { printf '  PASS  %s\n' "$1"; }
fail() { printf '  FAIL  %s\n' "$1"; failed=1; }
now_ms() { date +%s%3N; }

echo "Check 1: services healthy, /health ok through nginx"
for svc in postgres api frontend; do
  health=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{end}}' "$(docker compose ps -q "$svc")" 2>/dev/null || true)
  [ "$health" = healthy ] && pass "$svc healthy" || fail "$svc is '${health:-not running}'"
done
state=$(docker inspect -f '{{.State.Status}}' "$(docker compose ps -q worker)" 2>/dev/null || true)
[ "$state" = running ] && pass "worker running" || fail "worker is '${state:-not running}'"
body=$(curl -fsS "$BASE/health" || true)
case $body in *'"status":"ok"'*) pass "GET $BASE/health -> $body" ;; *) fail "GET $BASE/health -> '${body}'" ;; esac

echo "Check 2: SSE streams through nginx without buffering"
start=$(now_ms); first_delta=""; done_at=""; deltas=0
while IFS= read -r line; do
  case $line in
    "event: delta"*) deltas=$((deltas + 1)); [ -n "$first_delta" ] || first_delta=$(now_ms) ;;
    "event: done"*) done_at=$(now_ms) ;;
    "event: error"*) fail "chat returned an error event" ;;
  esac
done < <(curl -sSN -X POST "$BASE/api/v1/chat" -H 'Content-Type: application/json' -H 'X-Demo-User: ben' \
  --data "{\"question\": \"$QUESTION\"}")
if [ -z "$first_delta" ] || [ -z "$done_at" ]; then
  fail "no delta/done events (are the documents uploaded and Ready?)"
else
  echo "        $deltas deltas; first delta at $((first_delta - start)) ms, done at $((done_at - start)) ms"
  # Buffered, every event lands in one read at the end. Streamed, the first delta comes visibly earlier.
  [ $((done_at - first_delta)) -ge 50 ] && [ "$deltas" -gt 1 ] \
    && pass "first delta arrived $((done_at - first_delta)) ms before done" \
    || fail "deltas arrived together with done (buffered?)"
fi

echo "Check 3: the worker image parses offline (no network at all)"
worker_img=$(docker inspect -f '{{.Image}}' "$(docker compose ps -q worker)")
if docker run --rm --network none -v "$PWD/backend/tests/fixtures/serimaju:/fx:ro" "$worker_img" python -c '
import os
from pathlib import Path
from app.ingestion.chunking import hf_tokenizer
from app.ingestion.parsers.docling_parse import parse_docling
hf_tokenizer(os.environ["TOKENIZER_ID"])
parsed = parse_docling(Path("/fx/HR_Employee_Handbook_2024.pdf"), "pdf", os.environ["DOCLING_ARTIFACTS_PATH"])
assert parsed.full_text.strip(), "no text parsed"
print(f"        parsed {parsed.page_count} pages, {len(parsed.full_text)} chars offline")
'; then pass "Docling + tokenizer loaded with --network none"; else fail "worker needed the network or failed to parse"; fi

echo "Check 4: no secret in any image layer, image config or image filesystem"
key=$(sed -n 's/^AI_API_KEY=//p' .env 2>/dev/null | tr -d '\r"'"'" || true)
[ -n "$key" ] || echo "        (no AI_API_KEY in .env; checking for the variable name only)"
for svc in api worker frontend; do
  img=$(docker inspect -f '{{.Image}}' "$(docker compose ps -q "$svc")")
  hist=$(docker history --no-trunc --format '{{.CreatedBy}}' "$img")
  conf=$(docker image inspect -f '{{json .Config.Env}}' "$img")
  leak=0
  grep -q 'AI_API_KEY=.' <<<"$hist$conf" && leak=1
  [ -n "$key" ] && grep -qF "$key" <<<"$hist$conf" && leak=1
  if [ -n "$key" ]; then
    # The key goes in by env, never on the command line.
    docker run --rm --network none -e K="$key" --entrypoint sh "$img" -c \
      'test ! -e /app/.env && ! grep -rqsF "$K" /app /usr/share/nginx/html /etc/nginx 2>/dev/null' || leak=1
  fi
  [ $leak = 0 ] && pass "$svc image clean" || fail "$svc image holds a secret"
done

echo
[ $failed = 0 ] && echo "All SPEC-11 §6 checks 1–4 passed." || { echo "Some checks FAILED."; exit 1; }
