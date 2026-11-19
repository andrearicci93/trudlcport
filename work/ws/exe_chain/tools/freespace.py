"""freespace.py EXE - corse di zeri (>= 64 B) nelle sezioni aggiunte, in .shad e nella coda di .text, con controllo dei riferimenti:
abs = dword nel file con valore dentro la corsa (puntatori/indirizzi assoluti, anche dati a runtime come contatori o ring);
rel = destinazioni di call/jmp rel32 (E8/E9) che cadono nella corsa. Una corsa con riferimenti NON e' libera (e' un'area dati azzerata)."""
import sys, numpy as np, pefile
p = sys.argv[1] if len(sys.argv) > 1 else 'C:/tru-port/work/ws/b269_crash/tru_s8n_sap_cs2_cs.exe'
d = open(p, 'rb').read(); A = np.frombuffer(d, np.uint8)
pe = pefile.PE(p, fast_load=True)
secs = [(s.Name.rstrip(b'\0').decode(), s.PointerToRawData, s.SizeOfRawData, 0x400000 + s.VirtualAddress, s.Misc_VirtualSize, s.Characteristics) for s in pe.sections]
# tutti i dword (a ogni allineamento di byte) come valori
n = len(d) - 3
dw = (A[:n].astype(np.uint32) | (A[1:n + 1].astype(np.uint32) << 8) | (A[2:n + 2].astype(np.uint32) << 16) | (A[3:n + 3].astype(np.uint32) << 24))
# destinazioni rel32 di E8/E9 nelle sezioni eseguibili
tg = []
for nm, rp, rs, va, vs, ch in secs:
    if ch & 0x20000000:
        idx = np.nonzero((A[rp:rp + rs - 5] == 0xe8) | (A[rp:rp + rs - 5] == 0xe9))[0]
        rel = dw[rp + idx + 1].astype(np.int64); rel[rel >= 2**31] -= 2**32
        tg.append(va + idx + 5 + rel)
tg = np.concatenate(tg)
print('exe', p)
for nm, rp, rs, va, vs, ch in secs:
    if nm not in ('.text', '.shad', '.tuload', '.tuext', '.tufx', '.tufin'): continue
    lo = rp + (0x43c000 if nm == '.text' else 0)   # .text: solo l'ultima pagina (cave storiche 0x83c000..0x83e000)
    hi = rp + min(rs, max(vs, 1) if nm != '.text' else rs)
    z = (A[lo:hi] == 0).astype(np.int8)
    edges = np.diff(np.concatenate(([0], z, [0])))
    st, en = np.nonzero(edges == 1)[0], np.nonzero(edges == -1)[0]
    print('%s VA 0x%x vsize 0x%x raw 0x%x %s' % (nm, va, vs, rs, 'RWX' if ch & 0x80000000 and ch & 0x20000000 else ('RX' if ch & 0x20000000 else 'R/RW')))
    for a, b in zip(st, en):
        if b - a < 64: continue
        v0 = va + (lo - rp) + a; v1 = va + (lo - rp) + b
        nabs = int(np.count_nonzero((dw >= v0) & (dw < v1)))
        nrel = int(np.count_nonzero((tg >= v0) & (tg < v1)))
        print('   0x%x..0x%x  %5d B  abs=%d rel=%d %s' % (v0, v1, b - a, nabs, nrel, 'LIBERA?' if nabs == 0 and nrel == 0 else 'referenziata'))
