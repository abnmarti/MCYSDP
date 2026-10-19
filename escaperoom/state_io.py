"""Validated JSON persistence for game progress."""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from escaperoom.config import EXPECTED_EVIDENCE_FIELDS, REQUIRED_TOKENS, ROOM_SPECS
from escaperoom.models import GameState

SCHEMA_VERSION = 1
_HMAC_RE = re.compile(r"[0-9a-f]{64}\Z")


class InvalidSaveError(ValueError):
    """Raised when a save file is unreadable or violates the save schema."""


def _single_line(value: Any, label: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise InvalidSaveError(f"{label} must be a string")
    if (not value and not allow_empty) or "\n" in value or "\r" in value:
        raise InvalidSaveError(f"{label} must be a non-empty single-line string")
    return value


def state_to_dict(state: GameState) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "current_room": state.current_room,
        "tokens": dict(state.tokens),
        "evidence": {name: dict(values) for name, values in state.evidence.items()},
        "final_message": state.final_message,
        "final_hmac": state.final_hmac,
    }


def state_from_dict(payload: Any) -> GameState:
    if not isinstance(payload, dict):
        raise InvalidSaveError("save root must be a JSON object")
    version = payload.get("schema_version")
    if type(version) is not int or version != SCHEMA_VERSION:
        raise InvalidSaveError(f"unsupported save schema; expected version {SCHEMA_VERSION}")

    room = payload.get("current_room")
    if not isinstance(room, str) or room not in ROOM_SPECS:
        raise InvalidSaveError("current_room is not a known room")

    raw_tokens = payload.get("tokens")
    raw_evidence = payload.get("evidence")
    if not isinstance(raw_tokens, dict) or not isinstance(raw_evidence, dict):
        raise InvalidSaveError("tokens and evidence must be JSON objects")

    if not set(raw_tokens).issubset(REQUIRED_TOKENS):
        raise InvalidSaveError("save contains an unknown token name")
    if set(raw_evidence) != set(raw_tokens):
        raise InvalidSaveError("evidence entries must correspond exactly to collected tokens")

    tokens: dict[str, str] = {}
    evidence: dict[str, dict[str, str]] = {}
    for token_name, token_value in raw_tokens.items():
        tokens[token_name] = _single_line(token_value, f"token {token_name}")
        fields = raw_evidence[token_name]
        if not isinstance(fields, dict):
            raise InvalidSaveError(f"evidence for {token_name} must be a JSON object")
        expected_fields = set(EXPECTED_EVIDENCE_FIELDS[token_name])
        if set(fields) != expected_fields:
            raise InvalidSaveError(f"evidence fields for {token_name} do not match the required schema")
        evidence[token_name] = {
            key: _single_line(value, f"evidence {token_name}.{key}")
            for key, value in fields.items()
        }

    message = payload.get("final_message")
    digest = payload.get("final_hmac")
    if (message is None) != (digest is None):
        raise InvalidSaveError("final_message and final_hmac must either both be present or both be null")
    if message is not None:
        _single_line(message, "final_message")
        _single_line(digest, "final_hmac")
        if not REQUIRED_TOKENS.issubset(tokens):
            raise InvalidSaveError("final-gate result exists before all four tokens were collected")
        if not _HMAC_RE.fullmatch(digest):
            raise InvalidSaveError("final_hmac must be 64 lowercase hexadecimal characters")

    return GameState(
        current_room=room,
        tokens=tokens,
        evidence=evidence,
        final_message=message,
        final_hmac=digest,
    )


def _atomic_write(path: Path, content: str) -> None:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_name = handle.name
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)


def save_state(state: GameState, path: Path) -> None:
    if state.current_room not in ROOM_SPECS:
        raise ValueError("cannot save an unknown current room")
    serialized = json.dumps(state_to_dict(state), ensure_ascii=False, indent=2, sort_keys=True)
    _atomic_write(path, serialized + "\n")


def load_state(path: Path) -> GameState:
    path = path.expanduser()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"save file does not exist: {path}") from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidSaveError(f"could not read a valid UTF-8 JSON save from {path}: {exc}") from exc
    return state_from_dict(payload)
