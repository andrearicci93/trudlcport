"""Scansione: costanti float/double caricate (lis+lfs/lfd) che cambiano valore tra TU (tru_patched.bin) e base (tru_base.bin),
sulle coppie di funzioni di TU_DIFF.tsv (stato imm/mod). Allineamento per ordine dei caricamenti; riporta solo valori «normali».
uso: python tu_fconst_scan.py > out.tsv"""
import struct, math
X = 'C:/tru-port/work/xbox_exe/'
T = open(X + 'tru_patched.bin', 'rb').read(); B = open(X + 'tru_base.bin', 'rb').read()
def loads(d, a, n):
    w = lambda pc: struct.unpack_from('>I', d, pc - 0x82000000)[0]
    lis = {}; out = []
    for k in range(n):
        pc = a + 4 * k
        if pc - 0x82000000 + 4 > len(d): break
        x = w(pc); op = x >> 26; rt = (x >> 21) & 31; ra = (x >> 16) & 31; imm = x & 0xffff; simm = imm - 0x10000 if imm & 0x8000 else imm
        if op == 15 and ra == 0: lis[rt] = (imm << 16) & 0xffffffff; continue
        if op in (48, 50) and ra in lis:
            ea = (lis[ra] + simm) & 0xffffffff
            if 0x82000000 <= ea < 0x82000000 + len(d) - 8:
                v = struct.unpack_from('>f' if op == 48 else '>d', d, ea - 0x82000000)[0]
                out.append((pc, op, ea, v))
            continue
        # qualsiasi altra scrittura su rt invalida il lis (approssimazione: istruzioni con rt come destinazione)
        if op in (14, 24, 25, 31, 32, 33, 34, 35, 40, 41, 42, 43, 21, 28, 29) and rt in lis: lis.pop(rt, None)
    return out
import bisect
def starts(idx):
    r = []
    for l in open(X + idx):
        try: r.append(int(l.split('	')[0], 16))
        except ValueError: pass
    return sorted(r)
ST, SB = starts('decomp/INDEX.tsv'), starts('decomp_base/INDEX.tsv')
def flen(s, a):
    i = bisect.bisect_right(s, a); return min(((s[i] if i < len(s) else a + 0x400) - a) // 4, 3000)
def normal(v): return v == 0 or (1e-6 < abs(v) < 1e7 and not math.isnan(v))
n = 0
for l in open(X + 'TU_DIFF.tsv'):
    f = l.rstrip('\n').split('\t')
    if len(f) < 7 or f[3] not in ('imm', 'mod') or f[6] in ('-1', ''): continue
    ta = int(f[0], 16); ba = 0x82000000 + int(f[6], 16); sz = int(f[2])
    A = loads(T, ta, flen(ST, ta)); Bl = loads(B, ba, flen(SB, ba))
    if len(A) != len(Bl): continue
    for (pa, oa, ea, va), (pb, ob, eb, vb) in zip(A, Bl):
        if oa != ob or ea == eb or va == vb or not (normal(va) and normal(vb)): continue
        if va == 0 or vb == 0: continue
        print('%x\t%x\t%s\t%x\t%x\t%.6g\t%.6g\t%s' % (ta, ba, 'lfs' if oa == 48 else 'lfd', ea, eb, vb, va, f[3])); n += 1
import sys; print('TOTALE', n, file=sys.stderr)
