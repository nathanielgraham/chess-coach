#!/usr/bin/env python3
"""Rank weak spots from session stats plus optional engine motifs."""
from __future__ import annotations

from typing import Any


def _score(wins: int, losses: int, draws: int) -> float | None:
    n = wins + losses + draws
    if n <= 0:
        return None
    return (wins + 0.5 * draws) / n


def from_session(stats: dict[str, Any]) -> list[dict[str, Any]]:
    spots: list[dict[str, Any]] = []
    n = stats.get("n_used") or 0
    if n <= 0:
        return spots
    flags = stats.get("timeout_losses") or 0
    flag_rate = flags / n
    if flag_rate >= 0.15:
        spots.append({"id": "timeout_losses", "family": "clock", "n": flags, "rate": round(flag_rate, 3), "severity": "high" if flag_rate >= 0.25 else "medium", "evidence": f"{flags}/{n} games lost on time", "needs_engine": False})
    color = stats.get("color") or {}
    w = color.get("white") or {}
    b = color.get("black") or {}
    sw = _score(w.get("win", 0), w.get("loss", 0), w.get("draw", 0))
    sb = _score(b.get("win", 0), b.get("loss", 0), b.get("draw", 0))
    wn = sum(w.values()); bn = sum(b.values())
    if sw is not None and sb is not None and wn >= 15 and bn >= 15 and abs(sw - sb) >= 0.12:
        weak = "black" if sb < sw else "white"
        spots.append({"id": f"weak_{weak}", "family": "color", "n": bn if weak == "black" else wn, "rate": round(min(sw, sb), 3), "severity": "medium", "evidence": f"White {sw:.0%} vs Black {sb:.0%} ({wn} and {bn} games)", "needs_engine": False})
    by_tc = stats.get("by_tc") or {}
    if "180+0" in by_tc and any(k != "180+0" for k in by_tc):
        a = by_tc["180+0"]
        others = [v for k, v in by_tc.items() if k != "180+0"]
        a_n = a.get("games") or 0
        a_flags = (a.get("timeout_losses") or 0) / a_n if a_n else 0
        o_n = sum(x.get("games") or 0 for x in others)
        o_flags = sum(x.get("timeout_losses") or 0 for x in others) / o_n if o_n else 0
        if a_n >= 20 and o_n >= 8 and a_flags - o_flags >= 0.15:
            spots.append({"id": "increment_tourist", "family": "clock", "n": a.get("timeout_losses") or 0, "rate": round(a_flags, 3), "severity": "high", "evidence": f"3+0 timeout rate {a_flags:.0%} vs increment {o_flags:.0%}", "needs_engine": False})
    phase = stats.get("phase") or {}
    mid = (phase.get("mid") or {}).get("mean")
    overall = (stats.get("overall_think") or {}).get("mean")
    if mid and overall and mid >= overall * 1.6 and mid >= 5:
        spots.append({"id": "middlegame_overthink", "family": "clock", "n": (phase.get("mid") or {}).get("moves") or 0, "rate": None, "severity": "medium", "evidence": f"moves 11-25 mean {mid:.1f}s vs overall {overall:.1f}s", "needs_engine": False})
    return spots


def from_engine(engine: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not engine or not engine.get("available"):
        return []
    spots = []
    for tag, count in (engine.get("motifs") or {}).items():
        if count < 3:
            continue
        spots.append({"id": tag, "family": "move", "n": count, "rate": None, "severity": "high" if count >= 6 else "medium", "evidence": f"{count} engine-tagged misses", "needs_engine": True})
    acpl = engine.get("acpl")
    blunders = engine.get("blunders") or 0
    scored = engine.get("moves_scored") or 0
    if acpl is not None and scored >= 30 and acpl >= 80 and blunders >= 4:
        spots.append({"id": "high_acpl", "family": "move", "n": blunders, "rate": None, "severity": "medium", "evidence": f"ACPL {acpl} with {blunders} blunders on {scored} moves", "needs_engine": True})
    return spots


def rank(spots):
    weight = {"high": 3, "medium": 2, "low": 1}
    return sorted(spots, key=lambda s: (weight.get(s.get("severity"), 0), s.get("n") or 0), reverse=True)


def collect(stats):
    return rank(from_session(stats) + from_engine(stats.get("engine")))
