# Stockfish (optional)

Without an engine the coach still works: time, flags, color, openings.

With Stockfish it can also score move quality on a subset of games (default 15 games, ~80ms per position, skip the first 8 plies). That is how the bot tells flagged a won ending from blundered at move 18 in two seconds.

## If the user agrees to install

Debian/Ubuntu:

```bash
sudo apt-get update && sudo apt-get install -y stockfish
which stockfish
```

macOS (Homebrew):

```bash
brew install stockfish
which stockfish
```

Windows: install from https://stockfishchess.org/download/ and set STOCKFISH to the .exe path.

Or download an official binary and:

```bash
export STOCKFISH=/full/path/to/stockfish
```

Then rerun coach.py --engine auto.

## If they decline

--engine off. Do not invent ACPL. Say quality is inferred from results and flags only.

## How coaching uses a successful pass

Read stats.engine:

- acpl — average centipawn loss on the player's moves after ply 8
- blunders / mistakes / inaccuracies — 300 / 100 / 50 cp thresholds
- games_scored — sample size

Use it to rank bottlenecks against the clock stats. Example: high ACPL + low think time = tactics/pattern leak. Low ACPL + high timeout rate = conversion/clock leak. Do not treat shallow ACPL as a published rating.
