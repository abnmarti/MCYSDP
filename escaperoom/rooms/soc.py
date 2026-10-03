#Step 1: Read and Parse the Log File, For each line, we validate if it matches the exact required format
"""exact required format:
<TIMESTAMP> <HOST> sshd[<PID>]: <Failed|Accepted> password for <USER> from <IPv4> port <PORT> protocol 2"""
#Step 2: Extract Data from Valid Lines (valid Failed password record)
#Step 3: Find the Winning /24
#Step 4: Find the Most Frequent IP
#Step 5: Generate the KEYPAD
#Step 6: Output the Required Evidence

import re

ssh_reg = re.compile(
    r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\s+' + 
    r'(lab\d+)\s+' + 
    r'sshd\[(\d+)\]:\s+' + 
    r'(Failed|Accepted)\s+' + 
    r'password\s+for\s+(\w+)\s+' + 
    r'from\s+(\d{1,3}(?:\.\d{1,3}){3})\s+' + 
    r'port\s+(\d+)\s+' + 
    r'protocol\s+(\d+)'
)


def parse(line):
    m = ssh_reg.match(line)
    if not m: 
        return None 

    time_stamp, lab, pid, status, user, ip_address, port, protocol = m.group()


<<<<<<< HEAD
print(888888)

 
=======
print(5)
>>>>>>> 24a8a8f (test)
