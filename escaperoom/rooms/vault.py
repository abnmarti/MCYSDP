from dataclasses import dataclass
import re
from ..utils import PATH_VAULT
from .base import Room
@dataclass
class Vaultcandidate:
    matchedString: str
    a: int
    b: int
    c: int

safe_reg = re.compile(r'\bSAFE\s*\{(\s*\d+\s*)\-(\s*\d+\s*)\-(\s*\d+\s*)\}')

def read_file():
    with open(PATH_VAULT, 'r') as f: 
        return f.read()


def extract_all_candidates(content):
    candidates = []
    for match in safe_reg.finditer(content):
        a, b, c = map(int, match.groups())
        candidates.append(Vaultcandidate(matchedString=match.group(0), a=a, b=b, c=c))
    return candidates


def is_valid_candidate(candidate):
    return candidate.a + candidate.b == candidate.c


def get_candidate():
    content = read_file()
    candidates = extract_all_candidates(content)
    for candidate in candidates: 
        if is_valid_candidate(candidate):
            return candidate
    return None

class VaultRoom(Room):
    def __init__(self): 
        super().__init__(name="Vault Corridor", description="A noisy dump scrolls past. Somewhere a SAFE{a-b-c} hides.")

    def enter(self):
        print(f"you enter {self.name} - {self.description}")

    
    def inspect(self):
        print("[Room Vault] Scanning dump...")
        candidate = get_candidate()
        if is_valid_candidate(candidate):
            print(f"Found candidate: {candidate.matchedString}")
        else:
            raise ValueError(f"Invalid candidate: {candidate.matchedString}")
        print(f"Checksum: {candidate.a}+{candidate.b}={candidate.c} (OK)")
        print(f"TOKEN[SAFE]={candidate.a}-{candidate.b}-{candidate.c}")
        print(f'EVIDENCE[SAFE].MATCH="{candidate.matchedString}"')
        print(f"EVIDENCE[SAFE].CHECK={candidate.a}+{candidate.b}={candidate.c}")
