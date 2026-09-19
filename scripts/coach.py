#!/usr/bin/env python3
"""Fetch + analyze in one shot. Prints stats JSON path for the model to narrate."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
DEFAULT_PRIORS = SKILL / "references" / "priors.json"


def main() -> None:
    p = argparse.ArgumentParser(description="chess-coach fetch+analyze")
    p.add_argument("--platform", choices=["lichess", "chesscom"], required=True)
    p.add_argument("--user", required=True)
    p.add_argument("--max", type=int, default=80)
    p.add_argument("--perf", default="blitz")
    p.add_argument("--outdir", required=True)
    args = p.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    games_path = outdir / f"{args.user}_{args.platform}_{args.perf}.ndjson"
    stats_path = outdir / f"{args.user}_{args.platform}_{args.perf}_stats.json"

    fetch = [
        sys.executable,
        str(HERE / "fetch_games.py"),
        "--platform", args.platform,
        "--user", args.user,
        "--max", str(args.max),
        "--perf", args.perf,
        "--out", str(games_path),
    ]
    subprocess.check_call(fetch)
    analyze = [
        sys.executable,
        str(HERE / "analyze_games.py"),
        "--games", str(games_path),
        "--user", args.user,
        "--priors", str(DEFAULT_PRIORS),
        "--out", str(stats_path),
    ]
    subprocess.check_call(analyze)
    print(str(stats_path))


if __name__ == "__main__":
    main()
