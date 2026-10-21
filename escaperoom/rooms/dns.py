import base64
import codecs
from pathlib import Path

from escaperoom.models import PuzzleResult


def parse_config(content: str) -> dict[str, str]:
    #Read key=value lines, skipping comments.
    config = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if not key or not value:
            raise ValueError("Empty DNS key or value")
        if key in config:
            raise ValueError(f"Duplicate DNS key: {key}")
        config[key] = value
    return config


def decode_value(value: str) -> tuple[str, str]:
    #Return the encoding and decoded text.
    encoding, payload = value.split(":", 1)
    encoding, payload = encoding.strip(), payload.strip()

    if encoding == "rot13+b64":
        # Undo ROT13 before decoding Base64.
        payload = codecs.decode(payload, "rot_13")
    elif encoding != "b64":
        raise ValueError(f"Unknown encoding: {encoding}")

    text = base64.b64decode(payload, validate=True).decode("utf-8")
    return encoding, text


def solve_dns(data_dir: Path) -> PuzzleResult:
    config = parse_config((data_dir / "dns.cfg").read_text(encoding="utf-8"))
    _, tag = decode_value(config["token_tag"])
    if not tag.isascii() or not tag.isdecimal():
        raise ValueError("token_tag must decode to a hint number")

    hint_key = f"hint{tag}"
    encoding, decoded_line = decode_value(config[hint_key])

    if decoded_line.splitlines() != [decoded_line]:
        raise ValueError("The decoded hint must be one line")
    words = decoded_line.strip().removesuffix(".").split()
    if not words:
        raise ValueError("The decoded hint has no token")

    return PuzzleResult(
        token_name="DNS",
        token_value=words[-1],
        evidence={
            "KEY": hint_key,
            "ENCODING": encoding,
            "DECODED_LINE": decoded_line,
        },
    )
