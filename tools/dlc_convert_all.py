"""Convert DLC DRMs (Xbox, from work/generic/dlc_drms.pkl) to PC DRMs with dlc_generic.convert_drm and check them.

Checks per output DRM: parses back with drm_write.read (LE), reloc blobs parse + bounds (drm_reloc.check),
every id reference resolves (same DRM, PC base universe, or another converted DLC DRM), Obj section ids are
in the merged objectlist, route statistics per section type.
Usage: python3 -I tools/dlc_convert_all.py [--media] [--write] [name-substring ...]
  --media : use dlc_generic.default_media (textures/terrain/mesh/material/silent waves; shaders pass through)
  --write : write <out>/<name>.drm (CDRM, LE) to work/generic/out/
"""
import sys, os, pickle, struct, collections, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R, drm_write as DW, dlc_generic as DG, generic_store
W = DG.W

def check(secs, pc_ids, dlc_defined, objids):
    st = collections.Counter()
    infos = [dict(size=len(s.data)) for s in secs]
    have = {(s.type, s.id) for s in secs}
    for s in secs:
        r = R.parse(s.reloc, 'le')
        st['reloc_bounds_bad'] += bool(R.check(r, len(s.data), infos))
        for t, o in r.idref + r.idref_a:
            if o + 4 > len(s.data): continue
            v, = struct.unpack_from('<I', s.data, o)
            if v in (0, 0xffffffff): continue
            if (t, v) in have: st['idref_local'] += 1
            elif v in pc_ids.get(t, ()): st['idref_pc_base'] += 1
            elif (t, v) in dlc_defined: st['idref_other_dlc'] += 1
            else: st['idref_DANGLING'] += 1; st['dangling_type_%d' % t] += 1
        if s.type == 11: st['obj_ok' if s.id in objids else 'obj_BAD'] += 1
    return st

def main(argv):
    media = DG.default_media if '--media' in argv else None
    write = '--write' in argv
    pats = [a for a in argv if not a.startswith('--')]
    store = generic_store.load()
    dlc = pickle.load(open(os.path.join(W, 'dlc_drms.pkl'), 'rb'))
    ids = DG.DlcIds()
    T = DG.table()
    objids = set(json.load(open(os.path.join(W, 'merged', 'object_id_remap_xbox_to_pc.json'))).values())
    dlc_defined = {(s['type'], ids(s['type'], s['id'])) for _, (h, secs) in dlc.items() for s in secs}
    out = os.path.join(W, 'out'); os.makedirs(out, exist_ok=True)
    tot = collections.Counter(); routes = collections.Counter(); t0 = time.time()
    from archive import Archive
    from names import load, L
    from drm import cdrm_decode, sections_with_data
    xn = load(L + 'Tomb Raider Underworld (Xenon).txt')
    C = '/path/to/Xenia-SteveRepack/Content/534307EC/00000002/'
    packs = [C + '9CA70CF0EDA43654D158C2E37470D301DFA850E753/pack10.000', C + '600A12643FCDAC84003E6E0DBD0A1A8F7DAE9DD153/pack11.000']
    for pk in packs:
        A = Archive(pk, 'be')
        for r in A.idx:
            name = xn.get(r['hash'], '0x%08x' % r['hash']).split('\\')[-1]
            if pats and not any(p in name for p in pats): continue
            f = A.read(r)
            if f[:4] != b'CDRM' and f[:4] != b'\0\0\0\x13': continue
            raw = cdrm_decode(f, 'be')
            X = DW.read(raw, 'be')
            h, xsecs = sections_with_data(raw, 'be')
            secs, rep = DG.convert_drm(xsecs, ids, store, media=media, T=T)
            for k, t, xid, nid, route in rep: routes[t, route] += 1
            D = DW.Drm(secs, X.names, X.pad, X.ver, X.u0, X.u1)
            praw = D.write('le')
            back = DW.read(praw, 'le')
            tot['drm'] += 1
            tot['readback_ok'] += len(back.sections) == len(xsecs) and all(a.data == b.data and a.reloc == b.reloc for a, b in zip(back.sections, secs))
            tot.update(check(secs, store['pc_ids'], dlc_defined, objids))
            if write:
                sub = os.path.join(out, os.path.basename(pk).split('.')[0]); os.makedirs(sub, exist_ok=True)
                fn = name if name.endswith('.drm') else name + ('_%08x' % r['spec']) + '.drm'
                open(os.path.join(sub, fn), 'wb').write(DW.cdrm_encode(praw, 'le'))
    print('DRMs %d in %.0fs' % (tot['drm'], time.time() - t0))
    for k, v in sorted(tot.items(), key=str): print(' ', k, v)
    for k, v in sorted(routes.items(), key=str): print('  route', k, v)
    print('symbol stats', dict(ids.sym_stats), 'unmapped ids', dict(ids.missing))

if __name__ == '__main__':
    main(sys.argv[1:])
