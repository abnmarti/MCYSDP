from dataclasses import dataclass
from pathlib import Path
from escaperoom.models import PuzzleResult
import re

@dataclass
class Vaultcandidate:
    matchedString: str
    a: int
    b: int
    c: int

safe_reg = re.compile(r'\bSAFE\s*\{(\s*\d+\s*)\-(\s*\d+\s*)\-(\s*\d+\s*)\}')

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def extract_all_candidates(content):
    candidates = []
    for match in safe_reg.finditer(content):
        a, b, c = map(int, match.groups())
        candidates.append(Vaultcandidate(matchedString=match.group(0), a=a, b=b, c=c))
    return candidates


def is_valid_candidate(candidate):
    return candidate.a + candidate.b == candidate.c


def get_candidate(path):
    content = read_file(path)
    candidates = extract_all_candidates(content)
    for candidate in candidates:
        if is_valid_candidate(candidate):
            return candidate
    return None


def solve_vault(data_dir: Path) -> PuzzleResult:
    candidate = get_candidate(data_dir / "vault_dump.txt")
    if candidate is None:
        raise ValueError("No valid candidate found")

    return PuzzleResult(
        token_name="SAFE",
        token_value=f"{candidate.a}-{candidate.b}-{candidate.c}",
        evidence={
            "MATCH": candidate.matchedString,
            "CHECK": f"{candidate.a}+{candidate.b}={candidate.c}",
        },
    )

if __name__ == "__main__":
    from escaperoom.utils import DATA_PATH
    result = solve_vault(DATA_PATH)
    print("[Room Vault] Scanning dump...")
    print(f"Found candidate: {result.evidence["MATCH"]}")
    print(f"Checksum: {result.evidence["CHECK"]} (OK)")
    print(f"TOKEN[SAFE]={result.token_value}")
    print(f'EVIDENCE[SAFE].MATCH="{result.evidence["MATCH"]}"')
    print(f"EVIDENCE[SAFE].CHECK={result.evidence["CHECK"]}")
