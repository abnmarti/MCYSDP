import re
from ..utils import PATH_VAULT

safe_reg = re.compile(r'\bSAFE\s*\{(\s*\d+\s*)\-(\s*\d+\s*)\-(\s*\d+\s*)\}')

def read_file():
    with open(PATH_VAULT, 'r') as f: 
        l = f.read()
    return re.findall(safe_reg, l)
