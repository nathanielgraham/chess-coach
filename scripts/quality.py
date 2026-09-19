#!/usr/bin/env python3
"""Optional Stockfish move-quality pass."""
from __future__ import annotations

import os
import shutil
from typing import Any


def find_stockfish(explicit: str | None = None) -> str | None:
    if explicit and explicit not in ("auto", "off"):
        return explicit if os.path.isfile(explicit) and os.access(explicit, os.X_OK) else None
    env = os.environ.get("STOCKFISH")
    if env and os.path.isfile(env) and os.access(env, os.X_OK):
        return env
    for cand in ("stockfish", "stockfish-ubuntu-x86-64", "stockfish-x86-64"):
        found = shutil.which(cand)
        if found:
            return found
    for path in ("/usr/games/stockfish", "/usr/bin/stockfish"):
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


def _cp(info) -> int | None:
    if info is None or info.get("score") is None:
        return None
    score = info["score"].white()
    if score.is_mate():
        mate = score.mate()
        if mate is None:
            return None
        return 10000 if mate > 0 else -10000
    cp = score.score()
    return int(cp) if cp is not None else None


def analyze_quality(
    rows: list[dict],
    engine_path: str,
    max_games: int = 15,
    movetime_ms: int = 80,
    skip_plies: int = 8,
) -> dict[str, Any]:
    import chess
    import chess.engine

    sample = [r for r in rows if r.get("moves_san")][:max_games]
    cpl: list[int] = []
    blunders = mistakes = inaccuracies = 0
    games_ok = 0
    failed = 0

    try:
        eng = chess.engine.SimpleEngine.popen_uci(engine_path)
    except Exception as e:
        return {"available": False, "path": engine_path, "error": str(e)}

    limit = chess.engine.Limit(time=max(0.03, movetime_ms / 1000.0))
    try:
        for row in sample:
            board = chess.Board()
            me_white = bool(row.get("me_white", True))
            try:
                for ply, san in enumerate(row["moves_san"]):
                    try:
                        move = board.parse_san(san)
                    except ValueError:
                        break
                    is_me = (ply % 2 == 0 and me_white) or (ply % 2 == 1 and not me_white)
                    if ply >= skip_plies and is_me:
                        before = _cp(eng.analyse(board, limit))
                        board.push(move)
                        after = _cp(eng.analyse(board, limit))
                        if before is not None and after is not None:
                            pov = 1 if me_white else -1
                            loss = max(0, pov * before - pov * after)
                            cpl.append(int(loss))
                            if loss >= 300:
                                blunders += 1
                            elif loss >= 100:
                                mistakes += 1
                            elif loss >= 50:
                                inaccuracies += 1
                        continue
                    board.push(move)
                games_ok += 1
            except Exception:
                failed += 1
    finally:
        eng.quit()

    n = len(cpl)
    return {
        "available": True,
        "path": engine_path,
        "games_scored": games_ok,
        "games_failed": failed,
        "moves_scored": n,
        "acpl": round(sum(cpl) / n, 1) if n else None,
        "blunders": blunders,
        "mistakes": mistakes,
        "inaccuracies": inaccuracies,
        "movetime_ms": movetime_ms,
        "note": "Shallow search. Use as a leak finder, not a rating.",
    }


def engine_status(explicit: str | None = None) -> dict[str, Any]:
    if explicit == "off":
        return {"available": False, "reason": "disabled"}
    path = find_stockfish(explicit)
    if not path:
        return {
            "available": False,
            "reason": "stockfish not installed",
            "hint": "Install Stockfish and put it on PATH, or set STOCKFISH=/path/to/stockfish",
        }
    return {"available": True, "path": path}
