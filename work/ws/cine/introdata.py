"""Dati d'istanza delle intro (Intro+0x78 -> blob nel DTP di unita'): classi per (oggetto, offset) imparate dai livelli base
Xbox/PC (intro accoppiate per indice), confronto con l'overlay DLC. Cache coppie: introdata.pkl"""
import sys, os, struct, collections, pickle
T = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'); sys.path.insert(0, T)
import drm, drm_reloc as R, unit_ids as U
from archive import Archive
from names import crc
C = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'introdata.pkl')
CL = ('s32', 's16', 'raw', 'b2s16', 's16b2')
def conv(w, c): return {'s32': w[::-1], 's16': w[1::-1] + w[3:1:-1], 'raw': w, 'b2s16': w[0:2] + w[3:1:-1], 's16b2': w[1::-1] + w[2:4]}[c]
def secs(d, e): return drm.sections_with_data(drm.cdrm_decode(d, e), e)[1]
def blobs(sc, e):
    """[(objectID, blob bytes, slots relativi)] per intro con dati +0x78"""
    E = '>' if e == 'be' else '<'; L = U.level_info(sc, e); out = []
    if not L: return out
    for si, o in L['intros']:
        s = sc[si]; r = R.parse(s['reloc'], e); it = dict(r.internal)
        t = it.get(o + 0x78)
        if t is None: out.append(None); continue
        tg = sorted(set(it.values()) | {len(s['data'])}); end = min(x for x in tg if x > t)
        sl = {a - t for a in it if t <= a < end} | {b - t for _, b in r.idref if t <= b < end}
        out.append((struct.unpack_from(E + 'H', s['data'], o + 0x50)[0], s['data'][t:end], sl))
    return out
def pairs():
    if os.path.exists(C): return pickle.load(open(C, 'rb'))
    pcb = Archive(os.path.join(T, '..', 'pc', 'bigfile.000'), 'le')
    XB = [Archive('/path/to/TombRaiderUnderworld_Patched/layer%d.000' % i, 'be') for i in (1, 2)]
    names = [l.strip() for l in open(os.path.join(T, '..', 'ref', 'yura-release', 'FileLists', 'Tomb Raider Underworld (PC).txt'), errors='ignore')
             if l.strip().lower().startswith('pc-w\\') and l.strip().lower().endswith('.drm') and '\\' not in l.strip()[5:]]
    out = []
    for n in names:
        pr = pcb.find(crc(n)); xn = n.replace('pc-w', 'xenon-w')
        xd = next((A.read(A.find(crc(xn))[0]) for A in XB if A.find(crc(xn))), None)
        if not pr or xd is None: continue
        try:
            bx = blobs(secs(xd, 'be'), 'be'); bp = blobs(secs(pcb.read(pr[0]), 'le'), 'le')
        except Exception: continue
        if not bx or len(bx) != len(bp): continue
        for a, b in zip(bx, bp):
            if a and b and len(a[1]) == len(b[1]): out.append((n, a[0], a[1], a[2], b[1]))
    pickle.dump(out, open(C, 'wb')); return out
if __name__ == '__main__':
    P = pairs(); print('coppie blob intro base', len(P))
    # classe per (dimensione blob, offset) e per (prima parola, offset)
    tab = collections.defaultdict(collections.Counter)
    for n, oid, xd, sl, pd in P:
        for o in range(0, len(xd) - 3, 4):
            if o in sl: continue
            tab[(len(xd), xd[:4].hex(), o)][frozenset(c for c in CL if conv(xd[o:o + 4], c) == pd[o:o + 4])] += 1
    for k in sorted(tab):
        if k[0] == 0x30 and k[1] == '00000001':
            cnt = tab[k]; print(k, {tuple(sorted(s)) if len(s) < 5 else 'ANY': v for s, v in cnt.items()})
