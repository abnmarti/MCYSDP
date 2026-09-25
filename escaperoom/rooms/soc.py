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


print(5)

 
