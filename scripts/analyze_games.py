#!/usr/bin/env python3
"""Compute time and result stats from Lichess NDJSON or Chess.com monthly JSON lines."""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import Counter, defaultdict

CLK_RE = re.compile(r"\[%clk\s+(\d+):(\d+):(\d+(?:\.\d+)?)\]")
HDR_RE = re.compile(r'\[(\w+)\s+"([^"]*)"\]')


def load_ndjson(path: str) -> list[dict]:
    games = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                games.append(json.loads(line))
    return games


def detect_platform(game: dict) -> str:
    if "players" in game and "clocks" in game or game.get("perf") or game.get("speed"):
        if "white" in (game.get("players") or {}) and isinstance(game["players"].get("white"), dict):
            if "user" in game["players"]["white"] or "user" in game.get("players", {}).get("black", {}):
                return "lichess"
    if "pgn" in game and "time_class" in game:
        return "chesscom"
    if "clocks" in game:
        return "lichess"
    if "pgn" in game:
        return "chesscom"
    return "unknown"


def clk_to_sec(h, m, s) -> float:
    return int(h) * 3600 + int(m) * 60 + float(s)


def parse_tc_string(tc: str) -> tuple[int | None, int]:
    if not tc:
        return None, 0
    if "+" in str(tc):
        b, i = str(tc).split("+", 1)
        try:
            return int(b), int(i)
        except ValueError:
            return None, 0
    try:
        return int(tc), 0
    except ValueError:
        return None, 0


def thinks_from_rems(rems: list[float], base: float, inc: float, me_white: bool) -> tuple[list[float], list[float]]:
    thinks, mine = [], []
    w_prev = b_prev = float(base)
    for i, rem in enumerate(rems):
        white = i % 2 == 0
        prev = w_prev if white else b_prev
        think = prev + inc - rem
        if think < -0.4:
            think = 0.0
        think = max(0.0, min(float(think), 90.0))
        if (white and me_white) or ((not white) and (not me_white)):
            thinks.append(think)
            mine.append(rem)
        if white:
            w_prev = rem
        else:
            b_prev = rem
    return thinks, mine


def lichess_user_id(player: dict) -> str:
    u = player.get("user") or {}
    return (u.get("id") or u.get("name") or "").lower()


def parse_lichess(g: dict, user: str) -> dict | None:
    user = user.lower()
    players = g.get("players") or {}
    w, b = players.get("white") or {}, players.get("black") or {}
    me_w = lichess_user_id(w) == user
    me_b = lichess_user_id(b) == user
    if not (me_w or me_b):
        return None
    clk = g.get("clock") or {}
    base = float(clk.get("initial") or 0)
    inc = float(clk.get("increment") or 0)
    if not base:
        return None
    raw = g.get("clocks") or []
    rems = [c / 100.0 for c in raw]
    thinks, mine = thinks_from_rems(rems, base, inc, me_w)
    winner = g.get("winner")
    if winner is None:
        res = "draw"
    elif (winner == "white" and me_w) or (winner == "black" and me_b):
        res = "win"
    else:
        res = "loss"
    status = g.get("status") or ""
    timeout = status == "outoftime"
    opening = (g.get("opening") or {})
    return {
        "id": g.get("id"),
        "platform": "lichess",
        "tc": f"{int(base)}+{int(inc)}",
        "base": int(base),
        "inc": int(inc),
        "color": "white" if me_w else "black",
        "result": res,
        "status": status,
        "timeout_loss": timeout and res == "loss",
        "timeout_win": timeout and res == "win",
        "opening": opening.get("name"),
        "eco": opening.get("eco"),
        "thinks": thinks,
        "final": mine[-1] if mine else None,
        "n": len(thinks),
        "my_rating": (w if me_w else b).get("rating"),
        "opp_rating": (b if me_w else w).get("rating"),
    }


def parse_chesscom(g: dict, user: str) -> dict | None:
    user = user.lower()
    pgn = g.get("pgn") or ""
    headers = dict(HDR_RE.findall(pgn))
    white = (headers.get("White") or "").lower()
    black = (headers.get("Black") or "").lower()
    me_w = white == user
    me_b = black == user
    if not (me_w or me_b):
        return None
    raw_tc = g.get("time_control") or headers.get("TimeControl") or ""
    base, inc = parse_tc_string(raw_tc)
    if base is None:
        return None
    stamps = [clk_to_sec(*m) for m in CLK_RE.findall(pgn)]
    thinks, mine = thinks_from_rems(stamps, float(base), float(inc), me_w)
    res_raw = headers.get("Result") or ""
    if res_raw == "1/2-1/2":
        res = "draw"
    elif (res_raw == "1-0" and me_w) or (res_raw == "0-1" and me_b):
        res = "win"
    elif res_raw in ("1-0", "0-1"):
        res = "loss"
    else:
        res = "draw"
    term = (headers.get("Termination") or "").lower()
    timeout = "time" in term
    return {
        "id": g.get("url") or headers.get("Link"),
        "platform": "chesscom",
        "tc": f"{int(base)}+{int(inc)}",
        "base": int(base),
        "inc": int(inc),
        "color": "white" if me_w else "black",
        "result": res,
        "status": headers.get("Termination"),
        "timeout_loss": timeout and res == "loss",
        "timeout_win": timeout and res == "win",
        "opening": headers.get("Opening") or g.get("eco"),
        "eco": headers.get("ECO"),
        "thinks": thinks,
        "final": mine[-1] if mine else None,
        "n": len(thinks),
        "my_rating": (g.get("white") or {}).get("rating") if me_w else (g.get("black") or {}).get("rating"),
        "opp_rating": (g.get("black") or {}).get("rating") if me_w else (g.get("white") or {}).get("rating"),
    }


def summarize(thinks: list[float]) -> dict | None:
    if not thinks:
        return None
    s = sorted(thinks)
    n = len(s)
    return {
        "moves": n,
        "mean": round(statistics.mean(s), 3),
        "median": round(statistics.median(s), 3),
        "p90": round(s[int(0.9 * n)], 3),
        "pct_lt2": round(sum(t < 2 for t in s) / n, 4),
        "pct_lt5": round(sum(t < 5 for t in s) / n, 4),
        "pct_ge10": round(sum(t >= 10 for t in s) / n, 4),
        "pct_ge15": round(sum(t >= 15 for t in s) / n, 4),
    }


def load_priors(path: str | None) -> dict:
    if not path:
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def analyze(games: list[dict], user: str, priors: dict) -> dict:
    parsed = []
    for g in games:
        plat = detect_platform(g)
        row = parse_lichess(g, user) if plat == "lichess" else parse_chesscom(g, user)
        if row and row["n"] >= 4:
            parsed.append(row)

    by_tc: dict[str, list] = defaultdict(list)
    all_t: list[float] = []
    phase = {"open": [], "mid": [], "end": []}
    color = {"white": Counter(), "black": Counter()}
    openings: dict[str, Counter] = defaultdict(Counter)

    for r in parsed:
        by_tc[r["tc"]].append(r)
        all_t.extend(r["thinks"])
        phase["open"].extend(r["thinks"][:10])
        phase["mid"].extend(r["thinks"][10:25])
        phase["end"].extend(r["thinks"][25:])
        color[r["color"]][r["result"]] += 1
        if r.get("opening"):
            openings[r["opening"]][r["result"]] += 1

    def pack_group(rows: list[dict]) -> dict:
        thinks = [t for r in rows for t in r["thinks"]]
        finals = [r["final"] for r in rows if r["final"] is not None]
        rec = Counter(r["result"] for r in rows)
        return {
            "games": len(rows),
            "record": dict(rec),
            "think": summarize(thinks),
            "avg_ge10": round(statistics.mean(sum(t >= 10 for t in r["thinks"]) for r in rows), 3) if rows else None,
            "avg_ge15": round(statistics.mean(sum(t >= 15 for t in r["thinks"]) for r in rows), 3) if rows else None,
            "median_final": round(statistics.median(finals), 3) if finals else None,
            "pct_final_lt10": round(sum(x < 10 for x in finals) / len(finals), 4) if finals else None,
            "timeout_losses": sum(r["timeout_loss"] for r in rows),
            "timeout_wins": sum(r["timeout_win"] for r in rows),
            "prior": priors.get(rows[0]["tc"]) if rows else None,
        }

    open_tbl = []
    for name, c in openings.items():
        n = sum(c.values())
        if n < 3:
            continue
        open_tbl.append({
            "opening": name,
            "n": n,
            "win": c.get("win", 0),
            "loss": c.get("loss", 0),
            "draw": c.get("draw", 0),
            "score": round((c.get("win", 0) + 0.5 * c.get("draw", 0)) / n, 3),
        })
    open_tbl.sort(key=lambda x: (-x["n"], -x["score"]))

    return {
        "user": user,
        "n_input": len(games),
        "n_used": len(parsed),
        "record": dict(Counter(r["result"] for r in parsed)),
        "timeout_losses": sum(r["timeout_loss"] for r in parsed),
        "timeout_wins": sum(r["timeout_win"] for r in parsed),
        "overall_think": summarize(all_t),
        "phase": {k: summarize(v) for k, v in phase.items()},
        "color": {k: dict(v) for k, v in color.items()},
        "by_tc": {tc: pack_group(rows) for tc, rows in by_tc.items()},
        "openings_n3": open_tbl,
        "engine": None,
        "note": "No engine in v1. Quality inferred from results, flags, color, openings.",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--games", required=True)
    p.add_argument("--user", required=True)
    p.add_argument("--priors")
    p.add_argument("--out", required=True)
    args = p.parse_args()
    games = load_ndjson(args.games)
    priors = load_priors(args.priors)
    stats = analyze(games, args.user, priors)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    print(f"used {stats['n_used']}/{stats['n_input']} games, flags_me={stats['timeout_losses']}", file=sys.stderr)


if __name__ == "__main__":
    main()
