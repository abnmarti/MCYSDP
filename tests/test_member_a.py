from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from escaperoom.config import REQUIRED_DATA_FILES
from escaperoom.engine import GameEngine
from escaperoom.models import GameState, PuzzleResult
from escaperoom.state_io import InvalidSaveError, load_state, save_state, state_from_dict, state_to_dict
from escaperoom.transcript import Transcript


class StatePersistenceTests(unittest.TestCase):
    def test_round_trip_preserves_state(self) -> None:
        state = GameState(
            current_room="soc",
            tokens={"KEYPAD": "4217"},
            evidence={
                "KEYPAD": {
                    "TOP24": "203.0.113.0/24",
                    "COUNT": "17",
                    "SAMPLE": "sample auth line",
                    "MALFORMED_SKIPPED": "3",
                }
            },
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progress.json"
            save_state(state, path)
            restored = load_state(path)
        self.assertEqual(state_to_dict(state), state_to_dict(restored))

    def test_rejects_unknown_room_in_save(self) -> None:
        with self.assertRaises(InvalidSaveError):
            state_from_dict({
                "schema_version": 1,
                "current_room": "missing",
                "tokens": {},
                "evidence": {},
                "final_message": None,
                "final_hmac": None,
            })

    def test_rejects_evidence_not_matching_tokens(self) -> None:
        with self.assertRaises(InvalidSaveError):
            state_from_dict({
                "schema_version": 1,
                "current_room": "intro",
                "tokens": {"KEYPAD": "4217"},
                "evidence": {},
                "final_message": None,
                "final_hmac": None,
            })


class TranscriptTests(unittest.TestCase):
    def test_schema_tags_are_canonical_and_not_duplicated(self) -> None:
        state = GameState(
            current_room="soc",
            tokens={"KEYPAD": "4217"},
            evidence={
                "KEYPAD": {
                    "TOP24": "203.0.113.0/24",
                    "COUNT": "17",
                    "SAMPLE": "sample line",
                    "MALFORMED_SKIPPED": "3",
                }
            },
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "run.txt"
            transcript = Transcript(path)
            transcript.record("TOKEN[KEYPAD]=old-value")
            transcript.record("EVIDENCE[KEYPAD].COUNT=1")
            transcript.record("ordinary event")
            transcript.write(state)
            output = path.read_text(encoding="utf-8")
        self.assertEqual(output.count("TOKEN[KEYPAD]=4217"), 1)
        self.assertEqual(output.count("EVIDENCE[KEYPAD].COUNT=17"), 1)
        self.assertNotIn("old-value", output)
        self.assertIn("ordinary event", output)
        self.assertIn("FINAL_GATE=PENDING", output)


class EngineTests(unittest.TestCase):
    def _data_dir(self, root: Path) -> Path:
        data = root / "data"
        data.mkdir()
        for filename in REQUIRED_DATA_FILES:
            (data / filename).write_text("placeholder\n", encoding="utf-8")
        return data

    def test_move_solve_inventory_and_quit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = self._data_dir(root)
            transcript_path = root / "run.txt"
            outputs: list[str] = []
            commands = iter(["move soc", "inspect auth.log", "inventory", "quit"])
            result = PuzzleResult(
                token_name="KEYPAD",
                token_value="4217",
                evidence={
                    "TOP24": "203.0.113.0/24",
                    "COUNT": "17",
                    "SAMPLE": "sample line",
                    "MALFORMED_SKIPPED": "3",
                },
            )
            with patch.dict("escaperoom.engine.SOLVER_BY_ROOM", {"soc": lambda _path: result}):
                engine = GameEngine(
                    GameState(), data_dir, transcript_path,
                    input_fn=lambda _prompt: next(commands),
                    output_fn=outputs.append,
                )
                engine.run()
            self.assertEqual(engine.state.tokens["KEYPAD"], "4217")
            transcript = transcript_path.read_text(encoding="utf-8")
            self.assertEqual(transcript.count("TOKEN[KEYPAD]=4217"), 1)
            self.assertEqual(transcript.count("EVIDENCE[KEYPAD].COUNT=17"), 1)
            self.assertIn("You currently hold: KEYPAD=4217", "\n".join(outputs))

    def test_gate_requires_all_tokens(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = self._data_dir(root)
            outputs: list[str] = []
            commands = iter(["move final", "use gate", "quit"])
            engine = GameEngine(
                GameState(), data_dir, root / "run.txt",
                input_fn=lambda _prompt: next(commands),
                output_fn=outputs.append,
            )
            engine.run()
            self.assertTrue(any("Missing tokens" in line for line in outputs))
            self.assertIsNone(engine.state.final_hmac)


    def test_actual_group06_pack_starts_and_handles_pending_room_stub(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            transcript_path = Path(tmp) / "run.txt"
            completed = subprocess.run(
                [
                    sys.executable, "escape.py",
                    "--data", str(project_root / "data"),
                    "--transcript", str(transcript_path),
                ],
                input="move soc\ninspect auth.log\nquit\n",
                text=True,
                capture_output=True,
                cwd=project_root,
                timeout=10,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("[Integration pending]", completed.stdout)
            self.assertTrue(transcript_path.is_file())
            transcript = transcript_path.read_text(encoding="utf-8")
            self.assertIn("FINAL_GATE=PENDING", transcript)

    def test_unknown_command_does_not_crash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = self._data_dir(root)
            outputs: list[str] = []
            commands = iter(["teleport", "quit"])
            engine = GameEngine(
                GameState(), data_dir, root / "run.txt",
                input_fn=lambda _prompt: next(commands),
                output_fn=outputs.append,
            )
            engine.run()
            self.assertTrue(any("Unknown command" in line for line in outputs))


if __name__ == "__main__":
    unittest.main()
