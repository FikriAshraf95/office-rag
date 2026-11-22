# D009 — Vision instruction fixes the org-chart line format and asks for free-standing labels

- **Date / milestone:** 2026-11-21 · M07
- **Spec:** [SPEC-03 §8](../specs/SPEC-03-ingestion.md#8-images-and-vision-fallback-m07), [M07](../milestones/done/M07-vision-and-summaries.md)
- **Status:** Resolved → spec updated (folded at M99, 2026-11-21)

## Spec says
- The vision instruction is *"Extract all text. Then describe the structure (for org charts: every person, title and who they report to, one line per person). Do not add anything not visible."*

## Implementation does
- `VISION_INSTRUCTION` in `app/ingestion/vision.py` keeps that intent but is stricter:
  - "Extract all text, including captions and labels outside the boxes."
  - One line per person, top to bottom, in exactly the form `<Name>, <Title> - reports to <Name>, <Title>` (`- reports to no one` for the top person).
  - One extra line per caption that is not inside a box: `Label directly below the box of <Name>, <Title>: <label text>`, naming the box it sits closest to.

## Why
- Eval Q24 ("Who does the Finance team report to?") failed with the chart retrieved. The stored description had correct reporting lines but dropped the free-standing captions "Finance team (6 staff)" and "Engineering (~120 staff)" (Docling OCR returned no text for the image either). With no "Finance team" in the chunk, the answer model picked the CFO and answered with the CFO's own manager, which the judge read as a reversed line.
- A first try asked to end a person's line with `; leads <label>`; nemo-super attached "Finance team" to the CFO (an inference about leadership). Tying labels to a box by position only is a pure description of what is visible and came out right.

## Consequences
- Re-ingest images to get the new description (existing chunks keep the old one). The demo org chart was re-ingested on 2026-11-21.
- Fold the new wording into SPEC-03 §8 at M99.
