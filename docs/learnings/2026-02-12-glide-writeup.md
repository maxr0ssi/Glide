# Learnings — Glide Project Writeup

## What surprised us

- The existing docs (README, ARCHITECTURE.md, touchproof.md, DESIGN.md, learnings) covered almost every claim the writeup needed. Very little had to be inferred or invented — the documentation system paid off.
- The TouchProof fusion code actually uses 4 signals (proximity, angle, mfc, occlusion) but the occlusion/visibility signal is only 5% weight. Simplifying to 3 core signals for the writeup is accurate enough without misleading.

## Decisions made (and why)

- **Kept code snippets simplified but structurally faithful** — the Python fusion snippet mirrors the actual code at `touchproof.py:303-308` but drops the occlusion term and uses descriptive function names. Visitors don't need the full implementation, but it should feel real.
- **First person throughout** — matches the casual/technical mix requested. The opening and closing are storytelling, the middle sections are technical with diagrams and code.
- **"Building with AI" section is honest about limitations** — specifically calls out that human judgment was needed for feel/tuning, not just for correctness. This is more credible than "AI did everything perfectly."

## Follow-ups

- Review with real scrollable demo layout to check pacing — some sections may need trimming if the scroll area is narrow.
- ASCII diagrams should be tested in the actual renderer (some Markdown renderers handle box-drawing characters differently).

### PATCH SUMMARY
- Mode: Doing
- Changed files:
  - docs/writeups/glide-project.md (new)
  - docs/learnings/2026-02-12-glide-writeup.md (new)
- Why: Create narrative writeup of Glide project for personal website RHS panel
- How: Synthesized material from 7 source docs into 8-section narrative; verified all technical claims against source code and documentation
- Tests: Manual verification — all 17 technical claims cross-checked against source files
- Risks & Mitigations: ASCII diagrams may render differently in target site's Markdown renderer — test after integration
