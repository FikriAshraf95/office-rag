# D004 — Malay language line in the prompt (prompt v2)

- **Date / milestone:** 2026-11-21 · M04
- **Spec:** [SPEC-05 §2](../specs/SPEC-05-answering.md#2-prompt)
- **Status:** Resolved → spec updated

## Spec says
Prompt `v1`: the system prompt's rule 6 ("Answer in the language of the question") is the only language instruction. The user message ends with `Question: {question}`.

## Implementation does
`PROMPT_VERSION = "v2"`. When the question is detected as `ms`, the user message ends with one more line: `(The question is in Bahasa Malaysia: answer in Bahasa Malaysia.)`. Detection is `detect_language()` from SPEC-03 §6. Its Malay stop-word list now also has common question words (*saya, adakah, apakah, berapa, bagaimana, bila, siapa, perlu*), so a short question like Q28 counts as `ms` and not `mixed`. The not-found template uses the same detection.

## Why
In the M04 walkthrough on real ILMU, nemo-super (thinking off, temperature 0.1) answered Q28 *"Adakah saya perlu mengambil cuti tahunan pada 29 Disember 2026?"* in English with v1, although rule 6 was in the system prompt. With the extra line it answered in Malay on every try, and the English questions didn't change. Q28 is a success criterion (SPEC-00 §7).

## Consequences
SPEC-05 §2 now shows the line and `v2`. Mixed English/Malay questions (10–30 % Malay stop words) get no hint and fall back to rule 6. M06 eval runs record prompt v2.
