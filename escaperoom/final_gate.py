"""Member D's final-gate function; HMAC implementation is a team handoff."""

from pathlib import Path
from typing import Mapping

from escaperoom.models import FinalGateResult


def solve_final_gate(data_dir: Path, tokens: Mapping[str, str]) -> FinalGateResult:
    """Read final_gate.txt and return MSG plus its lowercase HMAC-SHA256.

    The function must read group_id, token_order, and hmac_key dynamically.
    `tokens` maps token names (KEYPAD, DNS, SAFE, PID) to discovered values.
    It must not hardcode a token order, message, key, or digest.
    """
    raise NotImplementedError(
        "Member D must implement solve_final_gate(data_dir, tokens)"
    )
