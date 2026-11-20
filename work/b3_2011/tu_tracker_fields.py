# B3 (TruXenia direct comparison): list TU code that loads the player tracker [0x829892b0] (lis 0x8299 / lwz -0x6d50)
# and then uses one of the wanted field offsets on that register - candidates for proof words of the tracker fields
# that TruMenu reads on PC (gt+0x78, +0xa20, +0xa64, +0x77c, +0xb00, +0xc94, +0xc98) and their +0x10 neighbours.
# Read only. Usage: ../bin/pyt work/b3_2011/tu_tracker_fields.py [listing] [out]
import re
import sys

LISTING = sys.argv[1] if len(sys.argv) > 1 else "work/asi/combat02/analysis/tu_all.txt"
OUT = sys.argv[2] if len(sys.argv) > 2 else "work/b3_2011/tu_tracker_fields.txt"
WANT = {0x78, 0x88, 0xa00, 0xa10, 0xa20, 0xa30, 0xa64, 0xa74, 0x77c, 0x78c, 0xb00, 0xb10, 0xc90, 0xca0, 0xc94, 0xca4,
        0xc98, 0xca8, 0x628, 0x504, 0x508, 0xf10, 0xf14}
WINDOW = 80
line_re = re.compile(r"^0x([0-9a-f]{8})\s+([0-9a-f]{8})\s+(\S+)\s*(.*)$")
mem_re = re.compile(r"^(r\d+|f\d+), (-?0x[0-9a-f]+|\d+)\(r(\d+)\)$")
load_re = re.compile(r"^r(\d+), -0x6d50\(r(\d+)\)$")
lis_re = re.compile(r"^r(\d+), -0x7d67$")


def dest(op, args):
    m = re.match(r"^r(\d+)", args)
    if not m:
        return None
    if op.startswith("st") or op.startswith("cmp") or op.startswith("b"):
        return None
    return int(m.group(1))


rows = []
with open(LISTING, "r", encoding="utf-8", errors="replace") as f:
    for ln in f:
        m = line_re.match(ln.rstrip("\n"))
        if m:
            rows.append((int(m.group(1), 16), m.group(2), m.group(3), m.group(4)))

hits = []
for i, (addr, word, op, args) in enumerate(rows):
    if op != "lwz":
        continue
    m = load_re.match(args)
    if not m:
        continue
    base = int(m.group(2))
    ok = False
    for k in range(max(0, i - 12), i):
        a2, w2, op2, ar2 = rows[k]
        lm = lis_re.match(ar2) if op2 == "lis" else None
        if lm and int(lm.group(1)) == base:
            ok = True
    if not ok:
        continue
    regs = {int(m.group(1))}
    for k in range(i + 1, min(len(rows), i + WINDOW)):
        a2, w2, op2, ar2 = rows[k]
        if op2 == "blr" or (op2 == "b" and k > i + 1):
            break
        mm = mem_re.match(ar2)
        if mm and int(mm.group(3)) in regs:
            off = int(mm.group(2), 16) if mm.group(2).startswith(("0x", "-0x")) else int(mm.group(2))
            if off in WANT:
                hits.append((addr, a2, w2, op2, ar2))
        if op2 == "mr":
            mr = re.match(r"^r(\d+), r(\d+)$", ar2)
            if mr and int(mr.group(2)) in regs:
                regs.add(int(mr.group(1)))
                continue
        d = dest(op2, ar2)
        if d is not None and d in regs:
            regs.discard(d)
        if not regs:
            break

with open(OUT, "w", encoding="utf-8", newline="\n") as o:
    o.write("load_at\tuse_at\tword\tinsn\n")
    for load_at, use_at, w, op, ar in hits:
        o.write("0x%08x\t0x%08x\t%s\t%s %s\n" % (load_at, use_at, w, op, ar))
counts = {}
for h in hits:
    key = h[4].split(", ")[1].split("(")[0]
    counts[key] = counts.get(key, 0) + 1
print("rows %d, tracker loads with field uses %d" % (len(rows), len(hits)))
for k in sorted(counts, key=lambda s: int(s, 16)):
    print("  %s %d" % (k, counts[k]))
print("out", OUT)
