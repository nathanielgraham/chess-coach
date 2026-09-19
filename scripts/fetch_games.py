#!/usr/bin/env python3
"""Fetch public rated games from Lichess or Chess.com to NDJSON."""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request

UA = "chess-coach/0.1 (public game review; contact: chess-coach)"


def http_get(url: str, headers: dict | None = None, timeout: int = 60) -> bytes:
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code} for {url}: {e.read()[:200]!r}") from e


def fetch_lichess(user: str, max_games: int, perf: str, rated: bool) -> list[dict]:
    params = [
        f"max={max_games}",
        f"perfType={perf}",
        "clocks=true",
        "opening=true",
        "moves=true",
    ]
    if rated:
        params.append("rated=true")
    url = f"https://lichess.org/api/games/user/{user}?{'&'.join(params)}"
    raw = http_get(url, headers={"Accept": "application/x-ndjson"})
    games = []
    for line in raw.decode("utf-8", errors="replace").splitlines():
        line = line.strip()
        if line:
            games.append(json.loads(line))
    return games


def fetch_chesscom(user: str, max_games: int, perf: str) -> list[dict]:
    user = user.lower()
    raw = http_get(f"https://api.chess.com/pub/player/{user}/games/archives")
    archives = json.loads(raw.decode()).get("archives") or []
    games: list[dict] = []
    for url in reversed(archives):
        time.sleep(0.25)
        payload = json.loads(http_get(url).decode())
        month = payload.get("games") or []
        for g in reversed(month):
            if perf and g.get("time_class") != perf:
                continue
            games.append(g)
            if len(games) >= max_games:
                return games
    return games


def main() -> None:
    p = argparse.ArgumentParser(description="Fetch public games to NDJSON")
    p.add_argument("--platform", choices=["lichess", "chesscom"], required=True)
    p.add_argument("--user", required=True)
    p.add_argument("--max", type=int, default=80)
    p.add_argument("--perf", default="blitz", help="blitz, bullet, rapid, ...")
    p.add_argument("--out", required=True)
    args = p.parse_args()

    if args.platform == "lichess":
        games = fetch_lichess(args.user, args.max, args.perf, rated=True)
    else:
        games = fetch_chesscom(args.user, args.max, args.perf)

    with open(args.out, "w", encoding="utf-8") as f:
        for g in games:
            f.write(json.dumps(g, separators=(",", ":")) + "\n")
    print(f"wrote {len(games)} games to {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
