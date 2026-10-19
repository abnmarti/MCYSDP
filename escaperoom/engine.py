"""Interactive game engine and integration layer for the Cyber Escape Room."""

from __future__ import annotations

import re
import sys
import traceback
from collections.abc import Callable, Mapping
from pathlib import Path

from escaperoom.config import (
    EXPECTED_EVIDENCE_FIELDS,
    REQUIRED_TOKENS,
    ROOM_ALIASES,
    ROOM_SPECS,
)
from escaperoom.final_gate import solve_final_gate
from escaperoom.models import FinalGateResult, GameState, PuzzleResult
from escaperoom.rooms.dns import solve_dns
from escaperoom.rooms.malware import solve_malware
from escaperoom.rooms.soc import solve_soc
from escaperoom.rooms.vault import solve_vault
from escaperoom.state_io import InvalidSaveError, load_state, save_state
from escaperoom.transcript import Transcript


SOLVER_BY_ROOM: dict[str, Callable[[Path], PuzzleResult]] = {
    "soc": solve_soc,
    "dns": solve_dns,
    "vault": solve_vault,
    "malware": solve_malware,
}
_TOKEN_BY_ROOM = {"soc": "KEYPAD", "dns": "DNS", "vault": "SAFE", "malware": "PID"}
_HMAC_RE = re.compile(r"[0-9a-f]{64}\Z")


class IntegrationError(ValueError):
    """Raised when a teammate's function violates the agreed return contract."""


class GameEngine:
    def __init__(
        self,
        state: GameState,
        data_dir: Path,
        transcript_path: Path,
        *,
        debug: bool = False,
        input_fn: Callable[[str], str] | None = None,
        output_fn: Callable[[str], None] | None = None,
    ) -> None:
        self.state = state
        self.data_dir = data_dir.expanduser().resolve()
        self.transcript = Transcript(transcript_path)
        self.debug = debug
        self._input = input_fn or input
        self._output = output_fn or print

    def emit(self, message: str = "") -> None:
        self._output(message)
        self.transcript.record(message)

    def run(self) -> None:
        self.emit("[Game] Cyber Escape Room started. Type 'help' for commands.")
        self._describe_current_room()
        should_continue = True

        while should_continue:
            try:
                raw = self._input("> ")
            except (EOFError, KeyboardInterrupt):
                self.emit("\n[Game] Input ended; closing the session.")
                break

            self.transcript.record_command(raw)
            if not raw.strip():
                continue
            should_continue = self.handle_command(raw)

        self.emit("[Game] Session ended.")
        try:
            self.transcript.write(self.state)
        except OSError as exc:
            self._output(f"[Error] Could not write transcript: {exc}")
            return
        self._output(f"[Game] Transcript written to {self.transcript.path}.")

    def handle_command(self, raw: str) -> bool:
        parts = raw.strip().split(maxsplit=1)
        if not parts:
            return True
        command = parts[0].casefold()
        argument = parts[1].strip() if len(parts) == 2 else ""

        if command in {"help", "?"}:
            self._help()
        elif command == "look":
            if argument:
                self.emit("Usage: look")
            else:
                self._describe_current_room()
        elif command == "move":
            self._move(argument)
        elif command == "inspect":
            self._inspect(argument)
        elif command == "use":
            self._use(argument)
        elif command == "inventory":
            self._inventory()
        elif command == "hint":
            if argument:
                self.emit("Usage: hint")
            else:
                self.emit(f"Hint: {ROOM_SPECS[self.state.current_room].hint}")
        elif command == "save":
            self._save(self._unquote(argument) if argument else "progress.json")
        elif command == "load":
            self._load(self._unquote(argument) if argument else "progress.json")
        elif command in {"quit", "exit"}:
            if argument:
                self.emit("Usage: quit")
                return True
            return False
        else:
            self.emit(f"Unknown command: {parts[0]}. Type 'help' for commands.")
        return True

    @staticmethod
    def _unquote(value: str) -> str:
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            return value[1:-1]
        return value

    def _help(self) -> None:
        self.emit(
            "Commands:\n"
            "  look                  describe the current room\n"
            "  move <room>           move to intro, soc, dns, vault, malware, or final\n"
            "  inspect <item>        analyze the current room's evidence item\n"
            "  use gate              run final verification in the Final Gate\n"
            "  inventory             show collected tokens\n"
            "  hint                  show a room-specific hint\n"
            "  save [file]           save progress (default: progress.json)\n"
            "  load [file]           load progress (default: progress.json)\n"
            "  quit                  end the game and write the transcript"
        )

    def _describe_current_room(self) -> None:
        spec = ROOM_SPECS[self.state.current_room]
        self.emit(spec.description)
        if spec.item and spec.key != "final":
            self.emit(f"Items here: {spec.item}")
        elif spec.key == "final":
            self.emit("Use: gate")

    def _move(self, argument: str) -> None:
        if not argument:
            self.emit("Usage: move <room>")
            return
        key = argument.casefold().strip()
        key = ROOM_ALIASES.get(key, key)
        if key not in ROOM_SPECS:
            choices = ", ".join(ROOM_SPECS)
            self.emit(f"Unknown room: {argument}. Available rooms: {choices}.")
            return
        self.state.current_room = key
        if key == "intro":
            self.emit("You return to the Intro Lobby.")
        else:
            self.emit(f"You enter the {ROOM_SPECS[key].title}.")
        self._describe_current_room()

    def _inventory(self) -> None:
        if not self.state.tokens:
            self.emit("You currently hold no tokens.")
            return
        items = ", ".join(f"{name}={value}" for name, value in sorted(self.state.tokens.items()))
        self.emit(f"You currently hold: {items}")

    @staticmethod
    def _validate_single_line(value: object, label: str) -> str:
        if not isinstance(value, str) or not value or "\n" in value or "\r" in value:
            raise IntegrationError(f"{label} must be a non-empty, single-line string")
        return value

    def _validate_puzzle_result(self, room: str, result: object) -> PuzzleResult:
        if not isinstance(result, PuzzleResult):
            raise IntegrationError("room function must return a PuzzleResult")
        expected_token = _TOKEN_BY_ROOM[room]
        if result.token_name != expected_token:
            raise IntegrationError(
                f"{room} function returned token {result.token_name!r}; expected {expected_token!r}"
            )
        self._validate_single_line(result.token_value, "token_value")
        if not isinstance(result.evidence, Mapping):
            raise IntegrationError("PuzzleResult.evidence must be a mapping")
        expected_fields = set(EXPECTED_EVIDENCE_FIELDS[expected_token])
        if set(result.evidence) != expected_fields:
            raise IntegrationError(
                f"evidence fields for {expected_token} must be exactly "
                f"{sorted(expected_fields)}; got {sorted(result.evidence)}"
            )
        for field, value in result.evidence.items():
            self._validate_single_line(value, f"evidence {expected_token}.{field}")
        return result

    def _inspect(self, argument: str) -> None:
        if not argument:
            self.emit("Usage: inspect <item>")
            return
        room = self.state.current_room
        spec = ROOM_SPECS[room]
        if room not in SOLVER_BY_ROOM:
            self.emit("There is no evidence item to inspect in this room.")
            return
        if argument.casefold() != spec.item.casefold():
            self.emit(f"That item is not available here. Items here: {spec.item}")
            return

        token_name = _TOKEN_BY_ROOM[room]
        if token_name in self.state.tokens:
            self.emit(f"This room has already been solved; token {token_name} is in your inventory.")
            return

        self.emit(f"[Room {spec.title}] Analyzing {spec.item}...")
        try:
            result = self._validate_puzzle_result(room, SOLVER_BY_ROOM[room](self.data_dir))
        except NotImplementedError as exc:
            self.emit(f"[Integration pending] {exc}")
            return
        except Exception as exc:
            if self.debug:
                traceback.print_exc(file=sys.stderr)
            self.emit(f"[Room error] {type(exc).__name__}: {exc}")
            return

        self.state.tokens[result.token_name] = result.token_value
        self.state.evidence[result.token_name] = dict(result.evidence)
        self.state.final_message = None
        self.state.final_hmac = None
        self.emit(f"Token formed: {result.token_value}")
        self.emit(f"TOKEN[{result.token_name}]={result.token_value}")
        for field in EXPECTED_EVIDENCE_FIELDS[result.token_name]:
            value = result.evidence[field]
            if (result.token_name, field) in {("SAFE", "MATCH"), ("PID", "CMD")}:
                value = f'"{value}"'
            self.emit(f"EVIDENCE[{result.token_name}].{field}={value}")

    def _use(self, argument: str) -> None:
        if argument.casefold() != "gate":
            self.emit("Usage: use gate")
            return
        if self.state.current_room != "final":
            self.emit("You must enter the Final Gate first.")
            return
        missing = sorted(REQUIRED_TOKENS - self.state.tokens.keys())
        if missing:
            self.emit(f"The gate is locked. Missing tokens: {', '.join(missing)}")
            return
        if self.state.final_message is not None and self.state.final_hmac is not None:
            self.emit("The Final Gate has already been processed for these tokens.")
            self.emit("FINAL_GATE=PENDING")
            self.emit(f"MSG={self.state.final_message}")
            self.emit(f"HMAC={self.state.final_hmac}")
            return

        self.emit("[Final Gate] Computing group-specific HMAC-SHA256...")
        try:
            result = solve_final_gate(self.data_dir, dict(self.state.tokens))
            self._validate_final_gate_result(result)
        except NotImplementedError as exc:
            self.emit(f"[Integration pending] {exc}")
            return
        except Exception as exc:
            if self.debug:
                traceback.print_exc(file=sys.stderr)
            self.emit(f"[Final Gate error] {type(exc).__name__}: {exc}")
            return

        self.state.final_message = result.message
        self.state.final_hmac = result.hmac_hex
        self.emit("FINAL_GATE=PENDING")
        self.emit(f"MSG={result.message}")
        self.emit(f"HMAC={result.hmac_hex}")

    def _validate_final_gate_result(self, result: object) -> FinalGateResult:
        if not isinstance(result, FinalGateResult):
            raise IntegrationError("final-gate function must return a FinalGateResult")
        self._validate_single_line(result.message, "final-gate message")
        self._validate_single_line(result.hmac_hex, "final-gate HMAC")
        if not _HMAC_RE.fullmatch(result.hmac_hex):
            raise IntegrationError("HMAC must be 64 lowercase hexadecimal characters")
        return result

    def _safe_output_path(self, filename: str) -> Path:
        path = Path(filename).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        path = path.resolve()
        protected = {(self.data_dir / name).resolve() for name in (
            "auth.log", "dns.cfg", "vault_dump.txt", "proc_tree.jsonl", "final_gate.txt"
        )}
        if path in protected:
            raise ValueError(f"refusing to overwrite source evidence: {path}")
        if path == self.transcript.path.expanduser().resolve():
            raise ValueError(f"refusing to overwrite the transcript with a save file: {path}")
        return path

    def _save(self, filename: str) -> None:
        if not filename:
            self.emit("Usage: save [file]")
            return
        try:
            path = self._safe_output_path(filename)
            save_state(self.state, path)
        except (OSError, ValueError) as exc:
            self.emit(f"[Save error] {exc}")
            return
        self.emit(f"[Game] Progress saved to {path}.")

    def _load(self, filename: str) -> None:
        if not filename:
            self.emit("Usage: load [file]")
            return
        try:
            path = Path(filename).expanduser()
            state = load_state(path)
        except (OSError, InvalidSaveError, ValueError) as exc:
            self.emit(f"[Load error] {exc}")
            return
        self.state = state
        self.emit(f"[Game] Progress loaded from {path.resolve()}.")
        self._describe_current_room()
        self._inventory()
