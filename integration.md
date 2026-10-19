# Integration guide

How to assemble the Cyber Escape Room from the four teammate modules.

## Required structure

This is the layout the framework expects. Commands run from the project root.

escape-room/                 ← run every command from here
├── escape.py                ← entry point
├── README.md
├── integration.md
├── .gitignore
├── data/                    ← the five group06 files, unchanged
│   ├── auth.log
│   ├── dns.cfg
│   ├── vault_dump.txt
│   ├── proc_tree.jsonl
│   └── final_gate.txt
├── escaperoom/
│   ├── __init__.py
│   ├── config.py
│   ├── engine.py
│   ├── models.py            ← PuzzleResult, FinalGateResult
│   ├── state_io.py
│   ├── transcript.py
│   ├── final_gate.py        ← Member D: solve_final_gate(data_dir, tokens)
│   └── rooms/
│       ├── __init__.py
│       ├── soc.py           ← Member B: solve_soc(data_dir)
│       ├── dns.py           ← Member C: solve_dns(data_dir)
│       ├── vault.py         ← Member C: solve_vault(data_dir)
│       └── malware.py       ← Member D: solve_malware(data_dir)
└── tests/
    └── test_member_a.py     ← teammates add test_soc.py, test_dns.py and so on here

## How to integrate your files

Each teammate's file replaces the stub at exactly that path, with exactly that function name.

- **Don't rename or move the files.** `engine.py` imports all five functions by name when it starts. A missing function, a wrong name or a syntax error in any one module stops the whole app before the lobby appears.
- **Import only from `escaperoom.models`.** A module needs nothing else from the package:


  from pathlib import Path
  from escaperoom.models import PuzzleResult        # FinalGateResult in final_gate.py


  Importing from `escaperoom.engine` creates a circular import, and the app won't start.
  
- **Don't print transcript tags.** The engine prints and records every `TOKEN[...]` and `EVIDENCE[...]` line itself. Tags printed by a solver show up twice on screen and are missing from `run.txt`.
- **Read only your own file**, at `data_dir / "<filename>"`.

## Function contract

Every evidence value must be a single-line `str`, with no trailing newline, so convert ints with `str()`.

| Module | Function | Token | Evidence keys |
|---|---|---|---|
| `rooms/soc.py` | `solve_soc(data_dir)` | `KEYPAD` | `TOP24`, `COUNT`, `SAMPLE`, `MALFORMED_SKIPPED` |
| `rooms/dns.py` | `solve_dns(data_dir)` | `DNS` | `KEY`, `ENCODING`, `DECODED_LINE` |
| `rooms/vault.py` | `solve_vault(data_dir)` | `SAFE` | `MATCH`, `CHECK` |
| `rooms/malware.py` | `solve_malware(data_dir)` | `PID` | `PATH`, `CMD`, `MALFORMED_SKIPPED` |
| `final_gate.py` | `solve_final_gate(data_dir, tokens)` | (returns `FinalGateResult(message, hmac_hex)`) | none |

The engine doesn't check the content of these values, so get the formats right:

| Field | Correct | Wrong |
|---|---|---|
| `TOP24` | `203.0.113.0/24` | `203.0.113.0/24/24`, `203.0.113` |
| `COUNT`, `MALFORMED_SKIPPED`, PID token | `"54"` (string) | `54` (int: rejected by the engine) |
| `PATH` | `[a->b->c]`, brackets included | `a->b->c` |
| `MATCH`, `CMD` | raw text **without** quotes (the engine adds them) | `"SAFE { … }"` (quotes doubled) |
| `CHECK` | `a+b=c` | `a+b=c (OK)` |
| DNS token | final word, period removed | `word.` |
| `message` | `<group_id from file>\|t1-t2-t3-t4` in `token_order` | literal `group_id\|…` |
| HMAC key | `hmac_key.encode("utf-8")` | `bytes.fromhex(hmac_key)` |

## Running the program

Use Homebrew's Python, version 3.11 or newer. The `auth.log` timestamps end in `Z`, and `datetime.fromisoformat` only accepts that from 3.11 onwards.

```bash
cd escape-room
python3 --version                      # must print 3.11 or newer

python3 -m unittest discover -s tests -v

python3 escape.py --start intro --data data --transcript run.txt
```

Then play through the rooms in the REPL:

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

When you type `quit`, the program writes `run.txt` and adds all the tagged lines once each at the end.

For a reproducible graded run, put the commands above in `demo_commands.txt` and pipe them in:

```bash
python3 escape.py --start intro --data data --transcript run.txt < demo_commands.txt
```

Make the graded `run.txt` in one fresh session that never uses `load`.

## Checklist for each teammate's module

1. **Run the tests.** `test_actual_group06_pack_starts_and_handles_pending_room_stub` will fail on purpose once Member B's code is in, because it expects the SOC room to still be a stub. Rewrite or delete it at that point.
2. **Inspect that teammate's room with `--debug`.** You get full tracebacks instead of one-line errors:

   ```bash
   python3 escape.py --debug
   ```
3. **Read any `[Room error] IntegrationError` message.** It names the exact contract breach. The most common are ints where strings are expected, and evidence keys with the wrong names.
4. **Check the formats from the table above against the transcript lines.** The engine doesn't check PATH brackets, MATCH and CMD quoting, the `TOP24` format or the `CHECK` format.
5. **Delete any old `progress.json` before the final run.** Loading a save restores old evidence, and the room then refuses to recompute it.
6. **Force-add the transcript before submitting:** `git add -f run.txt`. The `.gitignore` excludes it.

## Testing a module on its own

From the project root, run a module as part of the package:

```bash
python3 -m escaperoom.rooms.soc
```

Running `python3 escaperoom/rooms/soc.py` fails with `No module named 'escaperoom'`, because Python then treats `escaperoom/rooms/` as the top-level folder.
