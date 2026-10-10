from pathlib import Path

ROOT_PATH = Path(__file__).parent.parent

DATA_PATH = ROOT_PATH / "data"

PATH_VAULT = DATA_PATH / "vault_dump.txt"
PATH_AUTH = DATA_PATH / "auth.log"
PATH_DNS = DATA_PATH / "dns.cfg"
PATH_PROC_TREE = DATA_PATH / "proc_tree.jsonl"
PATH_GATE = DATA_PATH / "final_gate.txt"