"""TruTrace 0.3.3: compare the precheck byte strings with the code bytes in a crash dump (cdb `db` output of m.cdb),
so a site another loaded plugin patched at run time would show up. Read-only.

Usage (from trudlcport): ../bin/pyt -t 120 work/trutrace033_1411/dump_bytes_check.py PRECHECK.txt CDB_OUTPUT.txt
Exit 0 = all equal, 1 = a mismatch or a site missing in the dump output.
"""
import re
import sys


def main(argv):
    want = []
    for line in open(argv[0], encoding='utf-8'):
        line = line.split('#')[0].strip()
        if not line:
            continue
        addr, *hexes = line.split()
        want.append((int(addr, 16), bytes.fromhex(''.join(hexes))))
    mem = {}
    row = re.compile(r'^([0-9a-f]{8})  ((?:[0-9a-f]{2}[ -]){1,16})')
    for line in open(argv[1], encoding='utf-8', errors='replace'):
        m = row.match(line)
        if not m:
            continue
        base = int(m.group(1), 16)
        for k, b in enumerate(re.findall(r'[0-9a-f]{2}', m.group(2))):
            mem[base + k] = int(b, 16)
    bad = 0
    seen = set()
    for addr, data in want:
        if addr in seen:
            continue
        seen.add(addr)
        got = bytes(mem.get(addr + k, 0x100) & 0xff if (addr + k) in mem else 0 for k in range(len(data)))
        missing = any((addr + k) not in mem for k in range(len(data)))
        ok = not missing and got == data
        bad += 0 if ok else 1
        print('%-8s 0x%08x %2d bytes%s' % ('ok' if ok else 'MISMATCH', addr, len(data),
                                            '' if ok else ' found ' + (got.hex() if not missing else 'missing')))
    print('%d sites, %d mismatches' % (len(seen), bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
