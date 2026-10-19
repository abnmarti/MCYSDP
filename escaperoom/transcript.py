"""Console-event logging and canonical evidence transcript generation."""

from __future__ import annotations

from pathlib import Path

from escaperoom.config import (
    EXPECTED_EVIDENCE_FIELDS,
    TRANSCRIPT_TAG_PREFIXES,
    TRANSCRIPT_TOKEN_ORDER,
)
from escaperoom.models import GameState
from escaperoom.state_io import _atomic_write

_QUOTED_EVIDENCE_FIELDS = {("SAFE", "MATCH"), ("PID", "CMD")}


class Transcript:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._events: list[str] = []

    def record(self, text: str) -> None:
        """Record each physical line of visible console output."""
        self._events.extend(text.splitlines() or [""])

    def record_command(self, command: str) -> None:
        self._events.append(f"> {command}")

    @staticmethod
    def _is_schema_tag(line: str) -> bool:
        return line.startswith(TRANSCRIPT_TAG_PREFIXES)

    @staticmethod
    def _evidence_line(token_name: str, field: str, value: str) -> str:
        if (token_name, field) in _QUOTED_EVIDENCE_FIELDS:
            value = f'"{value}"'
        return f"EVIDENCE[{token_name}].{field}={value}"

    @classmethod
    def canonical_tag_lines(cls, state: GameState) -> list[str]:
        """Render the latest value for every completed puzzle exactly once."""
        lines: list[str] = []
        for token_name in TRANSCRIPT_TOKEN_ORDER:
            if token_name not in state.tokens:
                continue
            lines.append(f"TOKEN[{token_name}]={state.tokens[token_name]}")
            values = state.evidence[token_name]
            for field in EXPECTED_EVIDENCE_FIELDS[token_name]:
                lines.append(cls._evidence_line(token_name, field, values[field]))

        # The assignment's required schema uses this literal status value.
        lines.append("FINAL_GATE=PENDING")
        if state.final_message is not None and state.final_hmac is not None:
            lines.extend((f"MSG={state.final_message}", f"HMAC={state.final_hmac}"))
        return lines

    def write(self, state: GameState) -> None:
        # Puzzle evidence may have appeared during the interactive session.
        # Remove those event copies and append the latest canonical values once.
        events = [line for line in self._events if not self._is_schema_tag(line)]
        tags = self.canonical_tag_lines(state)
        if events and events[-1] != "":
            events.append("")
        events.extend(tags)
        _atomic_write(self.path, "\n".join(events).rstrip() + "\n")
