import hashlib
import hmac
from pathlib import Path
from typing import Mapping

from escaperoom.models import FinalGateResult


def solve_final_gate(data_dir: Path, tokens: Mapping[str, str]) -> FinalGateResult:
    #Build the final message and its HMAC 
    config = {}
    with open(data_dir / "final_gate.txt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip()
            if not key or not value:
                raise ValueError("Empty key or value")
            if key in config:
                raise ValueError(f"Duplicate final gate key: {key}")
            config[key] = value

    order = [name.strip() for name in config["token_order"].split(",")]
    if len(order) != 4 or set(order) != {"KEYPAD", "DNS", "SAFE", "PID"}:
        raise ValueError("token_order must list KEYPAD, DNS, SAFE and PID, 1 time each")

    message = config["group_id"] + "|" + "-".join(tokens[name] for name in order)
    digest = hmac.new(
        config["hmac_key"].encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return FinalGateResult(message=message, hmac_hex=digest)
