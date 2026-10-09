#Step 1: Read and Parse the Log File, For each line, we validate if it matches the exact required format
"""exact required format:
<TIMESTAMP> <HOST> sshd[<PID>]: <Failed|Accepted> password for <USER> from <IPv4> port <PORT> protocol 2"""
#Step 2: Extract Data from Valid Lines (valid Failed password record)
#Step 3: Find the Winning /24
#Step 4: Find the Most Frequent IP
#Step 5: Generate the KEYPAD
#Step 6: Output the Required Evidence


import re
import ipaddress
from collections import Counter
from datetime import datetime
from ..utils import PATH_AUTH

# ================= Global Variables =================
# Tracks the number of malformed/skipped records
MALFORMED_SKIPPED = 0
# Stores the first valid log sample encountered for each /24 subnet
SUBNET_SAMPLES = {}

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

def is_valid_iso8601(ts_str):
    """Strictly validate if the timestamp follows the ISO-8601 format."""
    try:
        # Compatible with the specific format required by the assignment
        datetime.strptime(ts_str, '%Y-%m-%dT%H:%M:%SZ')
        return True
    except ValueError:
        return False

# ================= Step 1: Read and Parse =================
def read_file(input_file):
    global MALFORMED_SKIPPED, SUBNET_SAMPLES
    MALFORMED_SKIPPED = 0
    SUBNET_SAMPLES = {}
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
                MALFORMED_SKIPPED += 1
                #malformed_skipped_content.append(clean_line)
                continue
                
            # Step 2: Extract data and perform strict validation
            if match.group('status').upper() == 'FAILED':
                ip = match.group('ip')
                ts = match.group('timestamp')
                
                # Requirement 1: Timestamp must be valid
                if not is_valid_iso8601(ts):
                    MALFORMED_SKIPPED += 1
                    #malformed_skipped_content.append(clean_line)
                    continue
                    
                # Requirement 2: IP must be valid
                if not is_valid_ipv4(ip):
                    MALFORMED_SKIPPED += 1
                    #malformed_skipped_content.append(clean_line)
                    continue
                    
                # Requirement 3: PID and PORT must be integers
                try:
                    int(match.group('pid'))
                    int(match.group('port'))
                except ValueError:
                    MALFORMED_SKIPPED += 1
                    #malformed_skipped_content.append(clean_line)
                    continue
                
                # All checks passed, store in dictionary
                record = match.groupdict()
                record['sample'] = clean_line  # Store the original log line for later SAMPLE output
                parsed_data.append(record)

                try:
                #one full valid failed-login line from the winning /24
                    subnet_key = str(ipaddress.IPv4Interface(f"{ip}/24").network)
                    SUBNET_SAMPLES.setdefault(subnet_key, clean_line)
                except ValueError:
                    pass
        #print(malformed_skipped_content) 
        print("===== Malformed / Skipped Lines =====")

    return parsed_data

# ================= Step 3: Get Subnet List =================
def get_subnets(parsed_data):
    subnet_list = []
    for item in parsed_data:
        ip = item.get('ip')
        if not ip:
            continue
        try:
            interface = ipaddress.IPv4Interface(f"{ip}/24")
            subnet = str(interface.network)
            subnet_list.append(subnet)
        except ValueError:
            continue
    return subnet_list

# ================= Step 4: Find Top /24 Subnet =================
def top_subnet(subnet_list):
    if not subnet_list:
        return None, 0    
    counter = Counter(subnet_list)
    max_subnet, max_subnet_count = counter.most_common(1)[0]
    return max_subnet, max_subnet_count

# ================= Step 5: Find Most Frequent Source IP in Top /24 =================
def get_frequent_sourceIP_subnet(parsed_data, max_subnet):
    ips_in_subnet = []
    # Handle cases where a tuple or a plain string might be passed
    target_subnet = max_subnet[0] if isinstance(max_subnet, tuple) else max_subnet
    
    for item in parsed_data:
        ip = item.get('ip')
        if not ip:
            continue
        subnet_x = '.'.join(ip.split('.')[:3]) + '.0/24'
        if subnet_x == target_subnet:
            ips_in_subnet.append(ip)
            
    if not ips_in_subnet:
        return None, 0
        
    frequent_sourceIP, max_sourceip_count = Counter(ips_in_subnet).most_common(1)[0]
    return frequent_sourceIP, max_sourceip_count

# ================= Step 6: Main Program and Output =================
if __name__ == "__main__":  
    # 1. Parse file
    parsed_data = read_file(PATH_AUTH)
    
    # 2. Get subnet list
    subnet_list = get_subnets(parsed_data)
    
    # 3. Find the TOP24 subnet
    top24_tuple = top_subnet(subnet_list)
    
    if top24_tuple[0]:
        top24_str, top24_count = top24_tuple
        
        # 4. Find the most frequent IP in this subnet
        frequent_ip, ip_count = get_frequent_sourceIP_subnet(parsed_data, top24_tuple)
        
        if frequent_ip:
            # 5. Extract the SAMPLE for this subnet (get the first valid sample from global variable)
            sample = SUBNET_SAMPLES.get(top24_str, "N/A")
            
            # 6. Calculate KEYPAD (Last octet of IP + total count)
            L = int(frequent_ip.split('.')[-1])
            keypad = f"{L}{top24_count}"
            
            # 7. Output according to specification
            print(f"TOKEN[KEYPAD]={keypad}")
            print(f"EVIDENCE[KEYPAD].TOP24={top24_str}")
            print(f"EVIDENCE[KEYPAD].COUNT={top24_count}")
            print(f"EVIDENCE[KEYPAD].SAMPLE={sample}")
            print(f"EVIDENCE[KEYPAD].MALFORMED_SKIPPED={MALFORMED_SKIPPED}")
        else:
            print("No valid failed log entries found in the top subnet.")
    else:
        print(f"TOKEN[KEYPAD]=N/A")
        print(f"EVIDENCE[KEYPAD].TOP24=N/A")
        print(f"EVIDENCE[KEYPAD].COUNT=0")
        print(f"EVIDENCE[KEYPAD].SAMPLE=N/A")
        print(f"EVIDENCE[KEYPAD].MALFORMED_SKIPPED={MALFORMED_SKIPPED}")