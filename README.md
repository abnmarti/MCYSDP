# Cyber Escape Room (MCYSDP)

A command-line escape room for the Programming Fundamentals project. You play a blue-team defender working through a simulated security incident. You move through five rooms, analyze the evidence file in each one and collect four tokens. At the Final Gate, the program combines the tokens into a group-specific HMAC-SHA256 proof.

The program uses only the Python standard library, and nothing is hardcoded: every token, piece of evidence and the final HMAC is computed from the files in `data/`.

## Requirements

- **Python 3.11 or newer.** The `auth.log` timestamps end in `Z`, and `datetime.fromisoformat` only accepts that from 3.11 onwards.
- No third-party packages, so there's nothing to `pip install`.

Check your version first (use `python3` instead of `python` on macOS/Linux if needed):

```bash
python --version
```

## Quick start

Run every command from the project root (the folder that contains `escape.py`).

```bash
python escape.py --start intro --data data --transcript run.txt
```

Then play through the rooms:

```text
move soc
inspect auth.log
move dns
inspect dns.cfg
move vault
inspect vault_dump.txt
move malware
inspect proc_tree.jsonl
move final
use gate
quit
```

When you type `quit`, the program writes `run.txt`.

### Non-interactive run

To get a repeatable transcript, put the commands above in a file (for example `demo_commands.txt`) and pipe it in:

```bash
python escape.py --start intro --data data --transcript run.txt < demo_commands.txt
```

Make the graded `run.txt` in one fresh session that never uses `load`. Loading a save restores old evidence, and a room that is already solved won't recompute it.

## Command-line options

| Option | Default | Description |
|---|---|---|
| `--start <room>` | `intro` | Room to start in: `intro`, `soc`, `dns`, `vault`, `malware` or `final` |
| `--data <dir>` | `data` | Folder containing the five data-pack files |
| `--transcript <file>` | `run.txt` | Where the transcript is written on exit |
| `--debug` | off | Show full tracebacks when a room fails, instead of a one-line error |

At startup the program checks that the data folder contains all five required files. It also refuses a transcript path that would overwrite one of them.

## REPL commands

| Command | Description |
|---|---|
| `help` / `?` | List the commands |
| `look` | Describe the current room |
| `move <room>` | Go to `intro`, `soc`, `dns`, `vault`, `malware` or `final`. Full names such as `malware lab` also work |
| `inspect <item>` | Analyze the evidence item in the current room |
| `use gate` | Run the final verification (only in the Final Gate, once all four tokens are collected) |
| `inventory` | Show the tokens collected so far |
| `hint` | Show a hint for the current room |
| `save [file]` | Save progress as JSON (default: `progress.json`) |
| `load [file]` | Load progress from a save file (default: `progress.json`) |
| `quit` / `exit` | End the game and write the transcript |

Ending input (Ctrl+D, Ctrl+Z on Windows, or Ctrl+C) also closes the session cleanly and still writes the transcript.

## The rooms

| Room | Input file | Token | What it does |
|---|---|---|---|
| SOC Triage Desk | `auth.log` | `KEYPAD` | Validates each SSH log line against the full required format with a strict regex and `ipaddress` checks, and counts malformed lines. It groups failed logins by `/24` and finds the busiest subnet, then the most frequent IP inside it. The token is `{last octet}{subnet failure count}` |
| DNS Closet | `dns.cfg` | `DNS` | Parses `key=value` lines and skips comments. It decodes `token_tag` to find out which `hintX` is authoritative, then reverses that hint's pipeline (`rot13+b64`: ROT13, then Base64, then UTF-8). The token is the last word of the decoded sentence |
| Vault Corridor | `vault_dump.txt` | `SAFE` | A compiled regex finds every `SAFE{a-b-c}` candidate, whatever its spacing. Only the candidate with `a + b == c` is kept, and the matched text is preserved as it appears |
| Malware Lab | `proc_tree.jsonl` | `PID` | Parses JSON lines and skips/counts malformed ones, then builds a `ppid -> [pid]` adjacency list. It runs both a recursive DFS and an iterative BFS from the root (`ppid == 0`), with a `visited` set so cycles can't cause infinite loops. It looks for the one command that meets the exfiltration contract (`curl -X POST ... -d @/tmp/x.tgz`, or `scp /tmp/x.tgz user@host:path`). Both searches must agree on the result |
| Final Gate | `final_gate.txt` | — | Reads `group_id`, `token_order` and `hmac_key`, builds `MSG = group_id\|t1-t2-t3-t4` in the given order, and computes HMAC-SHA256 with the UTF-8 key and message |

## Transcript (`run.txt`)

`run.txt` contains the whole session (commands and output). At the end it has exactly one canonical copy of each required tag. If a tag appeared earlier in the session, the earlier copies are removed so nothing is duplicated:

```text
TOKEN[KEYPAD]=...
EVIDENCE[KEYPAD].TOP24=...
EVIDENCE[KEYPAD].COUNT=...
EVIDENCE[KEYPAD].SAMPLE=...
EVIDENCE[KEYPAD].MALFORMED_SKIPPED=...
TOKEN[DNS]=...
EVIDENCE[DNS].KEY=hintX
EVIDENCE[DNS].ENCODING=...
EVIDENCE[DNS].DECODED_LINE=...
TOKEN[SAFE]=a-b-c
EVIDENCE[SAFE].MATCH="..."
EVIDENCE[SAFE].CHECK=a+b=c
TOKEN[PID]=...
EVIDENCE[PID].PATH=[p0->p1->...->pid]
EVIDENCE[PID].CMD="..."
EVIDENCE[PID].MALFORMED_SKIPPED=...
FINAL_GATE=PENDING
MSG=...
HMAC=...
```

The file is written atomically (to a temporary file, then renamed), so a crash can't leave a half-written transcript.

## Project structure

```text
MCYSDP/
├── escape.py              # Entry point: argument parsing and startup checks
├── README.md
├── integration.md         # How the team modules plug into the engine
├── run.txt                # Transcript of the graded run
├── data/                  # group06 data pack (do not modify)
│   ├── auth.log
│   ├── dns.cfg
│   ├── vault_dump.txt
│   ├── proc_tree.jsonl
│   └── final_gate.txt
├── escaperoom/
│   ├── config.py          # Room descriptions, hints, required files and evidence fields
│   ├── engine.py          # REPL, command handling, validation of room results
│   ├── models.py          # GameState, PuzzleResult, FinalGateResult
│   ├── state_io.py        # Validated JSON save/load with atomic writes
│   ├── transcript.py      # Session log and canonical tag output
│   ├── final_gate.py      # solve_final_gate(data_dir, tokens)
│   ├── utils.py           # Default data file paths
│   └── rooms/
│       ├── base.py        # Base Room class
│       ├── soc.py         # solve_soc(data_dir)
│       ├── dns.py         # solve_dns(data_dir)
│       ├── vault.py       # solve_vault(data_dir)
│       └── malware.py     # solve_malware(data_dir)
└── tests/
    └── test_member_a.py   # Engine, transcript and save/load tests
```

### Design

The engine and the puzzle logic are kept separate. Each room module exposes one function that takes the data folder and returns a `PuzzleResult` (token name, token value and an evidence dictionary). The engine:

- calls the right solver when you `inspect` an item;
- checks that the result follows the contract (right token name, exact evidence keys, non-empty single-line strings) and reports any breach as an `IntegrationError`;
- prints the `TOKEN[...]` and `EVIDENCE[...]` lines itself, so the solvers never print transcript tags.

This let each team member build and test their own room on its own. See `integration.md` for the full contract.

## Running the tests

```bash
python -m unittest discover -s tests -v
```

The tests cover save/load round trips and rejection of invalid saves, transcript de-duplication, the engine's move/inspect/inventory flow, the locked Final Gate, unknown commands, and a run against the real data pack.

> **Note:** `test_actual_group06_pack_starts_and_handles_pending_room_stub` was written while the SOC room was still a stub, and it expects an `[Integration pending]` message. Now that `soc.py` is implemented, this test fails on purpose (see `integration.md`) and should be rewritten or removed.

You can also run a single room module from the project root:

```bash
python -m escaperoom.rooms.soc
```

(Running `python escaperoom/rooms/soc.py` directly fails with `No module named 'escaperoom'`.)

## Troubleshooting

| Problem | Fix |
|---|---|
| `Startup error: missing required data file(s)` | Run from the project root, or point `--data` at the folder containing the five files |
| `[Room error] IntegrationError: ...` | A room returned data that breaks the contract. The message names the problem. Rerun with `--debug` for a traceback |
| Timestamp parsing errors in the SOC room | You're on Python older than 3.11. Upgrade |
| A room says it's already solved | You loaded a save that already has that token. Start a fresh session without `load` |

---

## AI disclosure

This README was written with the help of an AI assistant (Claude, by Anthropic). The assistant read the project's source code, the assignment brief and `integration.md`, and ran the program and test suite to check the documented behavior.
