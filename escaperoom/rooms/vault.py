from dataclasses import dataclass
import re
from ..utils import PATH_VAULT

@dataclass
class Vaultcandidate:
    matchedString: str
    a: int
    b: int
    c: int




safe_reg = re.compile(r'\bSAFE\s*\{(\s*\d+\s*)\-(\s*\d+\s*)\-(\s*\d+\s*)\}')

def read_file():
    with open(PATH_VAULT, 'r') as f: 
        line = f.read()
    return re.findall(safe_reg, line)


def checksum():
    content = read_file()
    i = 0
    a, b, c = map(int, content[i])
    while(a + b != c):
        return(f'Content: {content[i]}')
    i += 1 


print(checksum())