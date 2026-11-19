"""Scansione v2: costanti float/double (lis + lfs/lfd) con VALORE diverso tra TU (tru_patched.bin) e base (tru_base.bin).
Coppie di funzioni da TU_DIFF.tsv (imm/mod). Allineamento istruzione per istruzione con difflib sulle parole normalizzate (immediati e
spiazzamenti dei salti azzerati); il lis viene seguito per registro in ciascun flusso. Esclude le coppie con abbinamento dubbio
(stessa funzione base usata da piu' funzioni TU, rapporto strutturale < 0.85).
uso: python tu_fconst_scan2.py > tu_fconst2.tsv"""
import struct, math, bisect, difflib, collections, sys
X = 'C:/tru-port/work/xbox_exe/'
T = open(X + 'tru_patched.bin', 'rb').read(); B = open(X + 'tru_base.bin', 'rb').read()
def starts(idx):
    r = []
    for l in open(X + idx):
        try: r.append(int(l.split('\t')[0], 16))
        except ValueError: pass
    return sorted(r)
ST, SB = starts('decomp/INDEX.tsv'), starts('decomp_base/INDEX.tsv')
def flen(s, a):
    i = bisect.bisect_right(s, a); return min(((s[i] if i < len(s) else a + 0x400) - a) // 4, 4000)
DFORM = set(range(7, 16)) | set(range(24, 30)) | set(range(32, 64))
def norm(x):
    op = x >> 26
    if op in DFORM: return x & 0xffff0000
    if op == 18: return x & 0xfc000003
    if op == 16: return x & 0xffff0003
    return x
def decode(d, a, n):
    ws = [struct.unpack_from('>I', d, a - 0x82000000 + 4 * k)[0] for k in range(n)]
    lis = {}; ld = []
    for k, x in enumerate(ws):
        op = x >> 26; rt = (x >> 21) & 31; ra = (x >> 16) & 31; imm = x & 0xffff; simm = imm - 0x10000 if imm & 0x8000 else imm
        info = None
        if op == 15 and ra == 0: lis[rt] = (imm << 16) & 0xffffffff
        elif op == 14 and ra != 0 and ra in lis: lis[rt] = (lis[ra] + simm) & 0xffffffff   # addi su base lis (tabelle di costanti)
        elif op in (48, 50) and ra in lis:
            ea = (lis[ra] + simm) & 0xffffffff
            if 0x82000000 <= ea < 0x82000000 + len(d) - 8:
                info = (op, ea, struct.unpack_from('>f' if op == 48 else '>d', d, ea - 0x82000000)[0])
        else:
            if op in (14, 15, 32, 33, 34, 35, 40, 41, 42, 43, 31): lis.pop(rt, None)          # destinazione nel campo rt
            if op in (24, 25, 26, 27, 28, 29, 21, 20, 23, 30, 31): lis.pop(ra, None)          # logiche/rotazioni/mr: destinazione in ra
            if op in (18, 16, 19): lis.clear() if op == 18 and (x & 1) else None              # bl: registri volatili persi
        ld.append(info)
    return ws, ld
def normal(v): return not math.isnan(v) and not math.isinf(v) and (v == 0 or 1e-7 < abs(v) < 1e8)
rows = [l.rstrip('\n').split('\t') for l in open(X + 'TU_DIFF.tsv')]
rows = [f for f in rows if len(f) >= 7 and f[3] in ('imm', 'mod') and f[6] not in ('-1', '')]
cnt = collections.Counter(f[6] for f in rows)
n = 0; npair = 0
for f in rows:
    if cnt[f[6]] > 1: continue
    ta = int(f[0], 16); ba = 0x82000000 + int(f[6], 16)
    wt, lt = decode(T, ta, flen(ST, ta)); wb, lb = decode(B, ba, flen(SB, ba))
    sm = difflib.SequenceMatcher(None, [norm(x) for x in wt], [norm(x) for x in wb], autojunk=False)
    if sm.ratio() < 0.85: continue
    npair += 1
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            a, b = lt[blk.a + k], lb[blk.b + k]
            if not a or not b or a[0] != b[0] or a[2] == b[2]: continue
            if a[1] == b[1] or not (normal(a[2]) and normal(b[2])): continue
            print('%x\t%x\t%x\t%s\t%x\t%x\t%.7g\t%.7g\t%.3f' % (ta, ta + 4 * (blk.a + k), ba + 4 * (blk.b + k), 'lfs' if a[0] == 48 else 'lfd', a[1], b[1], b[2], a[2], sm.ratio())); n += 1
print('TOTALE', n, 'coppie esaminate', npair, 'su', len(rows), file=sys.stderr)
