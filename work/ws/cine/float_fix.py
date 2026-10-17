"""Corregge le parole float isolate convertite male nei DTP NUOVI del DLC (id >= 20000) -> swap s32.
Criterio: float Xbox plausibile con mantissa non tonda ((u & 0xfff) != 0), >= 2 vicini (+-4/8) float plausibili gia' s32 sul PC,
valore PC attuale = raw o s16 e come float LE implausibile. Solo questi byte cambiano (in place, stessa dimensione).
uso: float_fix.py SRC_MODS OUT_DIR [s16|raw]  (s16 = certo, default; raw = float rimasti con i byte Xbox)"""
import sys, os, struct, math, json
T = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'); sys.path.insert(0, T)
import drm, drm_reloc as R, drm_write as DW
from wave_swap import raw_dlc
def fval(b, e): return struct.unpack(e + 'f', b)[0]
def plaus(b, e='>', strict=True):
    v = fval(b, e); u = struct.unpack(e + 'I', b)[0]
    if not math.isfinite(v) or v == 0: return False
    ex = (u >> 23) & 0xff
    return 1e-3 <= abs(v) <= 1e5 and 100 <= ex <= 160 and (not strict or (u & 0xfff) != 0)
def main():
    src, out = sys.argv[1], sys.argv[2]; MODE = sys.argv[3] if len(sys.argv) > 3 else 's16'
    os.makedirs(out, exist_ok=True); log = []
    for f in sorted(os.listdir(src)):
        if not f.endswith('.drm') or 'costume' in f: continue
        xr, _ = raw_dlc(f)
        if xr is None: continue
        X = [s for s in drm.sections_with_data(drm.cdrm_decode(xr, 'be'), 'be')[1] if s['type'] == 7]
        D = DW.read(open(os.path.join(src, f), 'rb').read(), 'le')
        P = [s for s in D.sections if s.type == 7]
        if len(X) != len(P): continue
        changed = False
        for x, p in zip(X, P):
            if x['id'] < 20000: continue
            xd = x['data']; pd = bytearray(p.data)
            if len(xd) != len(pd): continue
            r = R.parse(x['reloc'], 'be'); sl = {a for a, _ in r.internal} | {o for _, o in r.idref}
            ok = lambda o: 0 <= o and o + 4 <= len(xd) and o not in sl and plaus(xd[o:o + 4], '>', False) and pd[o:o + 4] == xd[o:o + 4][::-1]
            for o in range(0, len(xd) - 3, 4):
                w = xd[o:o + 4]; cur = bytes(pd[o:o + 4])
                if o in sl or not plaus(w) or cur == w[::-1]: continue
                s16 = w[1::-1] + w[3:1:-1]
                if MODE == 's16' and cur != s16: continue                       # livello certo: solo coppie u16 scambiate
                if MODE == 'raw' and (cur != w or plaus(cur, '<', False)): continue  # livello probabile: float lasciati grezzi
                if MODE == 'raw' and o == 0x24 and w == bytes.fromhex('44444400'): continue  # Level+0x24: grezzo nel base (44/44)
                if sum(ok(o + d) for d in (-8, -4, 4, 8)) < 2: continue
                pd[o:o + 4] = w[::-1]; changed = True
                log.append(dict(file=f, dtp=x['id'], off=hex(o), xbox=w.hex(), prima=cur.hex(), dopo=w[::-1].hex(), valore=round(fval(w, '>'), 4)))
            p.data = bytes(pd)
        if changed: open(os.path.join(out, f), 'wb').write(DW.cdrm_encode(D.write('le'), 'le'))
    json.dump(log, open(os.path.join(out, 'float_fix_log.json'), 'w'), indent=1)
    import collections
    print('parole corrette', len(log), dict(collections.Counter((l['file'], l['dtp']) for l in log)))

if __name__ == '__main__':
    main()
