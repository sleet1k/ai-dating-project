import re

with open('tg_client.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

out = []
i = 0
while i < len(lines):
    line = lines[i]
    if 'print(f"\n' in line:
        line = line.replace('print(f"\n', 'print(f"\\n')
    if line.strip() == 'print(f"':
        if i + 1 < len(lines) and '\\033[' in lines[i+1]:
            line = lines[i].replace('print(f"', 'print(f"\\n') + lines[i+1].lstrip()
            i += 1
    # Find unterminated string
    if line.endswith('"\n') is False and line.endswith("'\n") is False and 'print(f"' in line:
        # maybe it spans lines
        pass
    out.append(line)

with open('tg_client.py', 'w', encoding='utf-8') as f:
    f.writelines(out)
