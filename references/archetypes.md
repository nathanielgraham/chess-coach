# Player archetypes

Pick at most one archetype as a lens, then still require the game sample to confirm it. Do not project a previous student's profile onto a new username.

## How to classify

Use whatever the platform exposes:

- Live rating for the control being reviewed (blitz, rapid, ...)
- Puzzle / tactics rating if present (Lichess perfs.puzzle)
- Timeout-loss rate in the sample
- Color split and opening split
- Think-time vs the control prior

Gaps under ~80 rating points are noise. Only treat puzzle vs live as a signal at ~150+ points.

## Common shapes

**Tactics ahead of games** (puzzle >> live).
They see motifs on a puzzle board and fail to use them with a clock. Usual bottleneck is conversion, flags, or refusing to move until the classical model is complete. Do not assign more Puzzle Storm.

**Games ahead of tactics** (live >> puzzle).
The more common club shape. They blitz out playable moves and hang tactics. Usual bottleneck is one-move tactics and a 4-question check before every move. Puzzles are the drill.

**Flag specialist** (timeout losses >15% of games).
Clock is the rating. Cap long sits; train endings on a 10s clock. Independent of puzzle rating.

**One-color player** (|White score - Black score| > 12 points on n>=40).
Patch the weak color first 10 moves only. Do not rebuild both repertoires.

**Opening scatter** (no family with n>=8 in 80 games).
They are inventing a new job every game. One White, one Black, 20 games. Not an opening-theory project.

**Increment tourist** (fine in 3+2 / 3+1, collapse in 3+0 / 5+0).
They can model positions when seconds refund. Teach the short model and a sit quota for no-increment.

**Quiet sample** (no flag problem, colors even, openings mixed).
Fall back to the rating-band ladder in by-rating.md.

## Output rule

Name the archetype in one line, then the evidence from this sample. If two lenses fit, pick the one with the higher estimated rating cost.
