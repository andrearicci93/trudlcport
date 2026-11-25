"""super_chain.py - (20/11/2026) solo lettura. Catena delle superclassi (root +0x18 id8 super) di script DLC sul PC (baseline) e
sull'Xbox, con vtableSize di ogni livello (PC: sezione nel DRM o nel generalbank PC; Xbox: sezione nel DRM Xbox o store base).
Segnala le superclassi la cui vtableSize differisce tra Xbox e PC (slot spostati). uso: super_chain.py BASELINE FILE.drm SID..."""
import sys, struct, pickle, json
sys.path.insert(0, '/path/to/trudlcport/work/ws/lukas_check/inv'); sys.path.insert(0, '/path/to/trudlcport/tools')
import inv_common as C, drm_write as DW, drm_reloc as R
BL, F = sys.argv[1:3]; SIDS = list(map(int, sys.argv[3:]))
S = pickle.load(open('/path/to/trudlcport/work/generic/store.pkl', 'rb'))
P = DW.read(open('/path/to/trudlcport/work/baseline/%s/mods/%s' % (BL, F), 'rb').read(), 'le'); X = DW.read(C.xbox(F), 'be')
GB, _ = C.pc_generalbank()
def find(secs, sid): return next((s for s in secs if s.type == 8 and s.id == sid), None)
def info(sec, e):
    E = '>' if e == 'be' else '<'; d = bytes(sec.data); r = R.parse(bytes(sec.reloc), e)
    ids = {o: t for t, o in list(r.idref) + list(r.idref_a)}
    sup = struct.unpack_from(E + 'I', d, 0x18)[0] if 0x18 in ids else None
    return struct.unpack_from(E + 'H', d, 0x3c)[0], sup
def chain(sid, side):
    out = []
    for _ in range(12):
        if side == 'pc':
            s = find(P.sections, sid) or find(GB, sid); src = 'drm' if find(P.sections, sid) else 'gb'
            if s is None: rec = S['pc_store'].get((8, sid)); s = DW.Section(8, sid, rec['data'], rec['reloc']) if rec else None; src = 'store'
            e = 'le'
        else:
            s = find(X.sections, sid); src = 'drm'
            if s is None: rec = S['xb_store'].get((8, sid)); s = DW.Section(8, sid, rec['data'], rec['reloc']) if rec else None; src = 'store'
            e = 'be'
        if s is None: out.append((sid, None, src)); break
        vt, sup = info(s, e); out.append((sid, vt, src))
        if sup is None or sup == sid: break
        sid = sup
    return out
for sid in SIDS:
    print('== script', sid); print('   PC  ', chain(sid, 'pc')); print('   Xbox', chain(sid, 'xb'))
