"""Application configuration and stable interfaces shared by the team."""

from __future__ import annotations

from dataclasses import dataclass


REQUIRED_DATA_FILES = (
    "auth.log",
    "dns.cfg",
    "vault_dump.txt",
    "proc_tree.jsonl",
    "final_gate.txt",
)

# These are the required token *names*, not the token_order used to form MSG.
REQUIRED_TOKENS = frozenset({"KEYPAD", "DNS", "SAFE", "PID"})

# This order is only for readable transcript output. The HMAC message must use
# token_order read dynamically from final_gate.txt by Member D's function.
TRANSCRIPT_TOKEN_ORDER = ("KEYPAD", "DNS", "SAFE", "PID")


@dataclass(frozen=True)
class RoomSpec:
    key: str
    title: str
    description: str
    item: str | None = None
    hint: str = ""


ROOM_SPECS = {
    "intro": RoomSpec(
        key="intro",
        title="Intro Lobby",
        description=(
            "You are in the Intro Lobby. Doors lead to: "
            "soc, dns, vault, malware, final."
        ),
        hint="Move to a room, then inspect its evidence item.",
    ),
    "soc": RoomSpec(
        key="soc",
        title="SOC Triage Desk",
        description="A terminal displays SSH authentication records.",
        item="auth.log",
        hint="Validate the complete log-line format. Count failed logins by /24, then find the most frequent IP inside the winning subnet.",
    ),
    "dns": RoomSpec(
        key="dns",
        title="DNS Closet",
        description="The walls are covered with key=value configuration records.",
        item="dns.cfg",
        hint="Decode token_tag first. It selects the authoritative hint; reverse each declared transformation in the correct order.",
    ),
    "vault": RoomSpec(
        key="vault",
        title="Vault Corridor",
        description="A noisy text dump contains SAFE candidates.",
        item="vault_dump.txt",
        hint="Use a compiled regular expression, preserve the matched text, and accept only the candidate for which a + b == c.",
    ),
    "malware": RoomSpec(
        key="malware",
        title="Malware Lab",
        description="A process tree contains parent-child relationships and decoy commands.",
        item="proc_tree.jsonl",
        hint="Build ppid -> pid edges, track visited PIDs, and verify the full exfiltration contract rather than matching only curl or scp.",
    ),
    "final": RoomSpec(
        key="final",
        title="Final Gate",
        description="The console asks for the four tokens and a group-specific proof.",
        item="gate",
        hint="Collect all four tokens. The gate function must read the group ID, token_order, and HMAC key from final_gate.txt.",
    ),
}

ROOM_ALIASES = {
    "lobby": "intro",
    "intro lobby": "intro",
    "soc triage desk": "soc",
    "dns closet": "dns",
    "vault corridor": "vault",
    "malware lab": "malware",
    "final gate": "final",
}

EXPECTED_EVIDENCE_FIELDS = {
    "KEYPAD": ("TOP24", "COUNT", "SAMPLE", "MALFORMED_SKIPPED"),
    "DNS": ("KEY", "ENCODING", "DECODED_LINE"),
    "SAFE": ("MATCH", "CHECK"),
    "PID": ("PATH", "CMD", "MALFORMED_SKIPPED"),
}

# These output tags are replaced by the canonical, latest values when the
# transcript is finalized. This prevents duplicates if a room is inspected again.
TRANSCRIPT_TAG_PREFIXES = (
    "TOKEN[KEYPAD]=",
    "TOKEN[DNS]=",
    "TOKEN[SAFE]=",
    "TOKEN[PID]=",
    "EVIDENCE[KEYPAD].",
    "EVIDENCE[DNS].",
    "EVIDENCE[SAFE].",
    "EVIDENCE[PID].",
    "FINAL_GATE=",
    "MSG=",
    "HMAC=",
)
