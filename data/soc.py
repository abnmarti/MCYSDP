with open('auth.log') as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    parts = line.split()
    if len(parts) < 13:
        print(f"line {i}: skipped, malformed ({len(parts)} fields)")
        continue
    ts, host, user, ip, port = parts[0], parts[1], parts[6], parts[8], parts[10]
    print(type(ts), type(host), type(user), type(ip), type(port))