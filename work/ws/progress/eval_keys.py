"""eval_keys.py - confronto di chiavi di raggruppamento per regole di larghezza, con validazione a 2 fold (per file sorgente) sulle coppie base.
Per ogni chiave K: regola (K, offset) = permutazione unica con >=N campioni (fold di training); predizione sul fold di test: copertura e accuratezza."""
import sys, os, collections, hashlib, zlib, pickle
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
import dtp_audit as DA, drm_reloc as R
def ph(xr): return hashlib.md5(repr(sorted(xr.internal)).encode()).hexdigest()[:10]
def region_fp(xd, xr):                      # impronta delle prime 4 parole non puntatore: distingue classi con stessa lunghezza
    sl = set(xr.pointer_offsets()) | set(xr.id_offsets()); w = []
    for o in range(0, min(len(xd), 64) - 3, 4):
        w.append(0 if o in sl else (1 if xd[o:o+4] != b'\0\0\0\0' else 2))
    return tuple(w)
KEYS = {
 'K1 len+ptr':      lambda xd, xr: (len(xd), ph(xr)),
 'K2 len':          lambda xd, xr: (len(xd),),
 'K3 ptr':          lambda xd, xr: (ph(xr),),
 'K4 len+head':     lambda xd, xr: (len(xd), region_fp(xd, xr)),
 'K5 w0+nptr+len//16': lambda xd, xr: (xd[:4], len(xr.internal), len(xd) // 16),
 'K6 w0+len':       lambda xd, xr: (xd[:4], len(xd)),
}
pairs = []
for x, p, xb, pc, xr in DA.base_pairs():
    pairs.append((zlib.crc32(xb['src'].encode()) & 1, xb['data'], pc['data'], xr))
print('coppie', len(pairs))
for name, kf in KEYS.items():
    for NMIN in (3, 5):
        stat = [collections.defaultdict(lambda: [0, 0, DA.ALL]) for _ in range(2)]   # (k,o) -> [n, nconf, cs]
        for f, xd, pd, xr in pairs:
            k = kf(xd, xr); sl = set(xr.pointer_offsets()) | set(xr.id_offsets())
            for o in range(0, len(xd) - 3, 4):
                if o in sl: continue
                c = DA.cls(xd[o:o+4], pd[o:o+4])
                if c in (0, DA.ALL): continue
                s = stat[f][(k, o)]; s[0] += 1; s[2] &= c
        tot = covered = right = wrong = 0
        for f, xd, pd, xr in pairs:
            k = kf(xd, xr); tr = stat[1 - f]; sl = set(xr.pointer_offsets()) | set(xr.id_offsets())
            for o in range(0, len(xd) - 3, 4):
                if o in sl: continue
                c = DA.cls(xd[o:o+4], pd[o:o+4])
                if c in (0, DA.ALL): continue
                tot += 1
                s = tr.get((k, o))
                if not s or s[0] < NMIN or bin(s[2]).count('1') != 1: continue
                covered += 1
                if c & s[2]: right += 1
                else: wrong += 1
        print('%-22s N>=%d  parole informative %7d  coperte %6.2f%%  accuratezza %8.4f%%  errori %d' % (name, NMIN, tot, 100*covered/max(1,tot), 100*right/max(1,covered), wrong))
