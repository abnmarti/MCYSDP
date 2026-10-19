"""Entry point for the Cyber Escape Room command-line application."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from escaperoom.config import REQUIRED_DATA_FILES, ROOM_SPECS
from escaperoom.engine import GameEngine
from escaperoom.models import GameState


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Play the Cyber Escape Room and collect evidence tokens."
    )
    parser.add_argument(
        "--start",
        choices=tuple(ROOM_SPECS),
        default="intro",
        help="room in which to start (default: intro)",
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("data"),
        help="directory containing the five group data files (default: data)",
    )
    parser.add_argument(
        "--transcript",
        type=Path,
        default=Path("run.txt"),
        help="where to write the final transcript (default: run.txt)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="show tracebacks when a room integration fails",
    )
    return parser.parse_args(argv)


def validate_data_directory(data_dir: Path) -> Path:
    """Return an absolute data path or raise a useful error."""
    resolved = data_dir.expanduser().resolve()
    if not resolved.is_dir():
        raise FileNotFoundError(f"data directory does not exist: {resolved}")

    missing = [name for name in REQUIRED_DATA_FILES if not (resolved / name).is_file()]
    if missing:
        names = ", ".join(missing)
        raise FileNotFoundError(f"missing required data file(s) in {resolved}: {names}")
    return resolved


def ensure_not_input_file(output_path: Path, data_dir: Path) -> None:
    """Prevent outputs from accidentally overwriting source evidence."""
    target = output_path.expanduser().resolve()
    protected = {(data_dir / name).resolve() for name in REQUIRED_DATA_FILES}
    if target in protected:
        raise ValueError(f"output path would overwrite a source data file: {target}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        data_dir = validate_data_directory(args.data)
        ensure_not_input_file(args.transcript, data_dir)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Startup error: {exc}", file=sys.stderr)
        return 2

    state = GameState(current_room=args.start)
    engine = GameEngine(
        state=state,
        data_dir=data_dir,
        transcript_path=args.transcript,
        debug=args.debug,
    )
    engine.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
