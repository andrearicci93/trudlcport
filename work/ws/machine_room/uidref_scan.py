"""uidref_scan.py - (20/11/2026) solo lettura. Cerca negli script (tipo 8) e nei DTP (tipo 7) dei DRM DLC2 della baseline e dei loro
sorgenti Xbox le parole u32 = uid delle intro indicate (Xbox BE, PC LE) e confronta le posizioni. uso: uidref_scan.py BASELINE uid..."""
import sys, struct, collections
sys.path.insert(0, '/path/to/trudlcport/work/ws/lukas_check/inv'); sys.path.insert(0, '/path/to/trudlcport/tools')
import inv_common as C, drm_write as DW
BL = sys.argv[1]; U = set(map(int, sys.argv[2:]))
for rel, path in C.files(BL):
    if not rel.startswith('dlc2'): continue
    xr = C.xbox(rel)
    P = DW.read(open(path, 'rb').read(), 'le'); X = DW.read(xr, 'be') if xr else None
    def hits(D, E):
        out = collections.defaultdict(list)
        for s in D.sections:
            if s.type not in (7, 8): continue
            d = bytes(s.data)
            for o in range(0, len(d) - 3, 4):
                v = struct.unpack_from(E + 'I', d, o)[0]
                if v in U: out[(s.type, s.id)].append((o, v))
        return out
    hp = hits(P, '<'); hx = hits(X, '>') if X else {}
    for k in sorted(set(hp) | set(hx)):
        a, b = hp.get(k, []), hx.get(k, [])
        print('%-34s %d:%-6d PC %3d Xbox %3d %s' % (rel, k[0], k[1], len(a), len(b), '' if [v for _, v in a] == [v for _, v in b] else 'DIVERSI'))
        if [v for _, v in a] != [v for _, v in b]: print('     PC', a[:12]); print('     XB', b[:12])
