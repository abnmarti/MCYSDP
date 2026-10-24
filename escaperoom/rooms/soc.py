#Step 1: Read and Parse the Log File, For each line, we validate if it matches the exact required format
"""exact required format:
<TIMESTAMP> <HOST> sshd[<PID>]: <Failed|Accepted> password for <USER> from <IPv4> port <PORT> protocol 2"""
#Step 2: get the subnet list
#Step 3: Find the Winning /24
#Step 4: Find the Most Frequent IP
#Step 5: Generate the KEYPAD and Output the Required Evidence

import re
import ipaddress
from escaperoom.models import PuzzleResult
from pathlib import Path
from collections import Counter
from ..utils import PATH_AUTH

# ================= Regex Pattern =================
line_parse = re.compile(r'''
    ^(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)
    \s+(?P<host>\S+)
    \s+sshd\[(?P<pid>\d+)\]:
    \s+(?P<status>Failed|Accepted)
    \s+password\ for\ (?P<user>\S+)
    \s+from\ (?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})
    \s+port\ (?P<port>\d+)
    \s+protocol\ 2$
''', re.VERBOSE)

# function for validation
def is_valid_ipv4(ip_str):
    """Strictly validate if an IPv4 address is legal using the standard library."""
    try:
        ipaddress.IPv4Address(ip_str)
        return True
    except ipaddress.AddressValueError:
        return False
    
_room_state = {"top_ip": None}

# ================= Step 1: Read and Parse =================
def read_file(input_file):
    malformed_skipped = 0
    subnet_samples = {}
    #malformed_skipped_content=[] 
    parsed_data = []
    # Use line-by-line reading to avoid memory overflow with large files
    with open(input_file, 'r', encoding='utf-8') as f: 
        for line in f:
            clean_line = line.strip()
            if not clean_line:
                continue

            match = line_parse.match(clean_line)
            if not match:
                malformed_skipped += 1
                #malformed_skipped_content.append(clean_line)
                continue
                
            # # Extract data and perform strict validation
            if match.group('status').upper() == 'FAILED':
                ip = match.group('ip')
                    
                # Requirement: IP must be valid
                if not is_valid_ipv4(ip):
                    malformed_skipped += 1
                    #malformed_skipped_content.append(clean_line)
                    continue
                
                # All checks passed, store in dictionary
                record = match.groupdict()
                record['sample'] = clean_line  # Store the original log line for later SAMPLE output

                subnet_key = str(ipaddress.IPv4Interface(f"{ip}/24").network)
                record['subnet'] = subnet_key
                subnet_samples.setdefault(subnet_key, clean_line)
                
                parsed_data.append(record)

        #print(malformed_skipped_content) 

    return parsed_data, malformed_skipped, subnet_samples

# ================= Step 2: Get Subnet List =================
def get_subnets(parsed_data):
    return [item['subnet'] for item in parsed_data if 'subnet' in item]

# ================= Step 3: Find Top /24 Subnet =================
def top_subnet(subnet_list):
    if not subnet_list:
        return None, 0    
    counter = Counter(subnet_list)
    max_subnet, max_subnet_count = counter.most_common(1)[0]
    return max_subnet, max_subnet_count

# ================= Step 4: Find Most Frequent Source IP in Top /24 =================
def get_frequent_sourceIP_subnet(parsed_data, max_subnet):
    ips_in_subnet = []
    # Handle cases where a tuple or a plain string might be passed
    target_subnet = max_subnet
    
    for item in parsed_data:
        if item.get('subnet') == target_subnet:
            ips_in_subnet.append(item['ip'])
            
    if not ips_in_subnet:
        return None, 0
        
    frequent_sourceIP, max_sourceip_count = Counter(ips_in_subnet).most_common(1)[0]
    return frequent_sourceIP, max_sourceip_count

def solve_soc(data_dir: Path) -> PuzzleResult:
    parsed_data, malformed_skipped, subnet_samples = read_file(data_dir / "auth.log")
    subnet_list = get_subnets(parsed_data)
    top24_tuple = top_subnet(subnet_list)
    _room_state["top_ip"] = None

    if top24_tuple[0]:
        top24_str, top24_count = top24_tuple
        frequent_ip, ip_count = get_frequent_sourceIP_subnet(parsed_data, top24_str)

        if frequent_ip:
            _room_state["top_ip"] = frequent_ip
            sample = subnet_samples.get(top24_str, "N/A")
            L = int(frequent_ip.split('.')[-1])
            keypad = f"{L}{top24_count}"
            

            return PuzzleResult(
                token_name="KEYPAD",
                token_value=keypad,
                evidence={
                    "TOP24": top24_str,
                    "COUNT": str(top24_count),
                    "SAMPLE": sample,
                    "MALFORMED_SKIPPED": str(malformed_skipped),
                        },
                )
        else:
            raise ValueError("No valid failed log entries found in the top subnet.")
    else:
        raise ValueError("No valid failed log entries found.")