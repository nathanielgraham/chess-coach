# Mistake types

When Stockfish is on, each drop of 100cp+ on the player's move is tagged. A tag that appears 3+ times in the engine sample is a bottleneck candidate. Do not invent motifs without stats.engine.motifs.

## Tags the script can emit

- backward_bishop / backward_knight / rook_retreat
- missed_capture / missed_queen / missed_rook
- poisoned_capture
- missed_check
- hung_piece
- tactical_line
- quiet_worsening

Use the top 1-2 tags with counts and one played-vs-best example. Without an engine, do not guess motifs from PGN memory.
