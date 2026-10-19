"""Small data structures exchanged between the engine and room functions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass
class GameState:
    current_room: str = "intro"
    tokens: dict[str, str] = field(default_factory=dict)
    evidence: dict[str, dict[str, str]] = field(default_factory=dict)
    final_message: str | None = None
    final_hmac: str | None = None


@dataclass(frozen=True)
class PuzzleResult:
    """Contract for each of the four analysis functions.

    `evidence` keys are suffixes such as "TOP24" or "MATCH". The engine adds
    the `EVIDENCE[TOKEN].` prefix when displaying and writing the transcript.
    """

    token_name: str
    token_value: str
    evidence: Mapping[str, str]


@dataclass(frozen=True)
class FinalGateResult:
    """Contract for Member D's final-gate/HMAC function."""

    message: str
    hmac_hex: str
