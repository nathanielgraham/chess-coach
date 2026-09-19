# chess-coach

Grok skill + CLI that pulls public Lichess or Chess.com games, scores time use against control priors, slices by color and opening, and picks one or two bottlenecks.

Works for any public username. Classification uses *that* sample (flags, color, openings, think vs prior, puzzle vs live when the site exposes it). It does not assume a high-puzzle / low-blitz profile.

## Install for Grok

Copy this folder to:

- `.grok/skills/chess-coach/` in a project, or
- `~/.grok/skills/chess-coach/`

Python 3.10+, stdlib only. Network required for fetch.

## CLI

```bash
python3 scripts/coach.py \
  --platform lichess \
  --user SOMEONE \
  --max 80 \
  --perf blitz \
  --outdir ./out
```

`--platform chesscom` works the same. The command prints a `*_stats.json` path. With the skill loaded, Grok reads that file and writes the short report.

## v1 scope

Clocks, results, flags, color, openings, archetypes. No Stockfish. No live-move help during a rated game.

## Layout

```
SKILL.md
scripts/fetch_games.py
scripts/analyze_games.py
scripts/coach.py
references/priors.json
references/time-management.md
references/report-template.md
references/by-rating.md
references/archetypes.md
```

## License

MIT
