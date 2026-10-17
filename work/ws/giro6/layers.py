"""Giro 6: costruzione a STRATI di B89 (derivata da B88b_acqua). Ogni strato legge la versione corrente dei file (albero giro6/tree se gia' toccato, altrimenti B88b)
e scrive solo i file cambiati in giro6/tree/<rel>. Strati: L1 (texture 259/2224 nei DRM che le puntano).  Uso: layers.py L1"""
import sys, os, json, struct, hashlib, glob
ROOT = '/path/to/trudlcport'; sys.path.insert(0, ROOT + '/tools')
import drm, drm_write as DW, drm_reloc as R
from archive import Archive
B88 = ROOT + '/work/baseline/B88b_acqua/mods'; TREE = ROOT + '/work/ws/giro6/tree'
def cur(rel):
    p = os.path.join(TREE, rel); return p if os.path.exists(p) else os.path.join(B88, rel)
def put(rel, raw):
    p = os.path.join(TREE, rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'wb').write(raw)
def base_tex(tid):
    """sezione (5,tid) dal gioco base PC: (data, ver, flags, spec) -- prima occorrenza; verifica md5 identico su tutte."""
    d = json.load(open(ROOT + '/work/idx_pc.json')); got = {}
    for e in d:
        if isinstance(e[5], list) and any(s[0] == 5 and s[1] == tid for s in e[5]):
            a = Archive(e[0], 'le'); raw = drm.cdrm_decode(a.read(a.idx[e[1]]), 'le')
            for s in drm.sections_with_data(raw, 'le')[1]:
                if s['type'] == 5 and s['id'] == tid: got.setdefault((hashlib.md5(s['data']).hexdigest(), s['ver'], s['flags'], s['spec']), s['data'])
        if len(got) > 1: break
    assert len(got) == 1, (tid, list(got))
    (md, ver, fl, sp), data = next(iter(got.items())); return data, ver, fl, sp, md
def add_tex(rel, tid, tex):
    data, ver, fl, sp, md = tex
    raw = open(cur(rel), 'rb').read(); d = DW.read(DW.cdrm_decode(raw, 'le') if raw[:4] == b'CDRM' else raw, 'le')
    assert (5, tid) not in {(s.type, s.id) for s in d.sections}, (rel, tid)
    n0 = len(d.sections)
    mx = max((si for x in d.sections for si, _, _ in R.parse(x.reloc, 'le').external), default=-1)
    assert mx < n0, (rel, mx, n0)       # nessuna reloc esterna puo' puntare alla nuova sezione in coda
    ref = next(s for s in d.sections if s.type == 5)
    d.sections.append(DW.Section(5, tid, data, b'', flags=fl, ver=ver, spec=sp, pad=ref.pad))
    out = DW.cdrm_encode(d.write('le'), 'le'); put(rel, out)
    a = {(s.type, s.id): s for s in DW.read(DW.cdrm_decode(raw, 'le') if raw[:4] == b'CDRM' else raw, 'le').sections}
    b = {(s.type, s.id): s for s in DW.read(DW.cdrm_decode(out, 'le'), 'le').sections}
    assert set(b) - set(a) == {(5, tid)} and set(a) <= set(b)
    for k, x in a.items(): assert (b[k].data, b[k].reloc, b[k].flags, b[k].ver, b[k].spec) == (x.data, x.reloc, x.flags, x.ver, x.spec), (rel, k)
    print('  ', rel, '+(5,%d) %d B md5 %s ver %d flags %d' % (tid, len(data), md[:8], ver, fl), hashlib.md5(out).hexdigest()[:8])
def L1():
    t259 = base_tex(259); t2224 = base_tex(2224)
    for c in 'bcefjo': add_tex('dlc_costume_%s.drm' % c, 259, t259)
    add_tex('doppelganger.drm', 2224, t2224)

# ---- L2: dead-bit (uid >= 16352 -> uid liberi < 16352) -----------------------------------------------------------
UIDMAP = {29392: 12241, 29397: 12242, 29395: 12243, 29396: 12244, 26713: 12245}
L2REFS = {   # (DRM, tipo, id sezione, offset) -> uid vecchio ; DTP = Intro (+0x58), script = operando
    ('dlc_level1_start.drm', 7, 26889, 1160): 29392, ('dlc_level1_start.drm', 7, 26889, 3320): 29397,
    ('dlc_level1_start.drm', 8, 20068, 2196): 29392, ('dlc_level1_start.drm', 8, 20083, 420): 29392, ('dlc_level1_start.drm', 8, 20084, 420): 29392,
    ('dlc_dungeon.drm', 7, 20258, 52088): 29395, ('dlc_dungeon.drm', 7, 20258, 19256): 29396, ('dlc_dungeon.drm', 8, 20419, 5124): 29395,
    ('dlc_dungeonhallb.drm', 7, 20133, 1272): 26713, ('dlc_dungeonhallb.drm', 8, 20171, 724): 26713}
def L2():
    byrel = {}
    for (rel, t, i, o), u in L2REFS.items(): byrel.setdefault(rel, []).append((t, i, o, u))
    for rel, items in sorted(byrel.items()):
        raw = open(cur(rel), 'rb').read(); d = DW.read(DW.cdrm_decode(raw, 'le') if raw[:4] == b'CDRM' else raw, 'le')
        for t, i, o, u in items:
            s = next(x for x in d.sections if x.type == t and x.id == i)
            assert struct.unpack_from('<I', s.data, o)[0] == u, (rel, t, i, o)
            # la parola non deve essere una posizione di relocation
            rr = R.parse(s.reloc, 'le') if s.reloc else None
            if rr: assert all(o != off for grp in (rr.idref,) for _, off in grp), (rel, t, i, o)
            b = bytearray(s.data); struct.pack_into('<I', b, o, UIDMAP[u]); s.data = bytes(b)
        out = DW.cdrm_encode(d.write('le'), 'le'); put(rel, out)
        a = {(x.type, x.id): x for x in DW.read(DW.cdrm_decode(raw, 'le') if raw[:4] == b'CDRM' else raw, 'le').sections}
        b = {(x.type, x.id): x for x in DW.read(DW.cdrm_decode(out, 'le'), 'le').sections}
        assert set(a) == set(b)
        chg = {k for k in a if a[k].data != b[k].data}
        assert chg == {(t, i) for t, i, o, u in items}, (rel, chg)
        for k in a: assert (a[k].reloc, a[k].flags, a[k].ver, a[k].spec) == (b[k].reloc, b[k].flags, b[k].ver, b[k].spec)
        nb = sum(1 for k in chg for x, y in zip(a[k].data, b[k].data) if x != y)
        print('  ', rel, 'sezioni cambiate', sorted(chg), 'byte diversi', nb, hashlib.md5(out).hexdigest()[:8])


# ---- L3a: lib 975/976 (PS/VS del materiale 20262) nei 2 streamgroup dungeon che usano il materiale ma non le contengono ------
def copy_sections(rel, src_rel, specs, after):
    """aggiunge in rel le sezioni (tipo,id) di specs prese (byte per byte, con flags/ver/spec/pad/reloc) da src_rel, subito dopo la sezione `after` (tipo,id)."""
    src = {(x.type, x.id): x for x in DW.read(DW.cdrm_decode(open(cur(src_rel), 'rb').read(), 'le'), 'le').sections}
    raw = open(cur(rel), 'rb').read(); d = DW.read(DW.cdrm_decode(raw, 'le') if raw[:4] == b'CDRM' else raw, 'le')
    names = {(x.type, x.id) for x in d.sections}
    pos = next(i for i, x in enumerate(d.sections) if (x.type, x.id) == after)
    mx = max((si for x in d.sections for si, _, _ in R.parse(x.reloc, 'le').external), default=-1)
    assert mx < pos, (rel, mx, pos)      # nessun indice esterno dopo il punto di inserimento
    for k, key in enumerate(specs):
        assert key not in names, (rel, key)
        x = src[key]; assert not x.reloc
        d.sections.insert(pos + 1 + k, DW.Section(x.type, x.id, x.data, x.reloc, flags=x.flags, ver=x.ver, spec=x.spec, pad=x.pad))
    out = DW.cdrm_encode(d.write('le'), 'le'); put(rel, out)
    a = {(x.type, x.id): x for x in DW.read(DW.cdrm_decode(raw, 'le') if raw[:4] == b'CDRM' else raw, 'le').sections}
    b = {(x.type, x.id): x for x in DW.read(DW.cdrm_decode(out, 'le'), 'le').sections}
    assert set(b) - set(a) == set(specs) and set(a) <= set(b)
    for k, x in a.items(): assert (b[k].data, b[k].reloc, b[k].flags, b[k].ver, b[k].spec) == (x.data, x.reloc, x.flags, x.ver, x.spec), (rel, k)
    print('  ', rel, '+', specs, hashlib.md5(out).hexdigest()[:8])
def L3a():
    for rel in ('streamgroups/dlc_dungeon_dungeon_main.drm', 'streamgroups/dlc_dungeon_dungeon_sewer.drm'):
        copy_sections(rel, 'dlc_caverns.drm', [(9, 975), (9, 976)], (9, 332))


# ---- L3b: lib dedicata del materiale 20323 (knight_thrall) con DXN completo sul registro Xbox 8 (build_20323.py, lib 2782) ----------
def L3b():
    src = ROOT + '/work/ws/giro6/out_20323_full/mods'
    for rel in ('co_dlc_knight_thrall.drm', 'co_dlc_knight_thrall_pieces.drm', 'knight_thrall.drm', 'knight_thrall_chunkdoll.drm'):
        new = open(os.path.join(src, rel), 'rb').read(); old = open(cur(rel), 'rb').read()
        a = {(x.type, x.id): x for x in DW.read(DW.cdrm_decode(old, 'le'), 'le').sections}
        b = {(x.type, x.id): x for x in DW.read(DW.cdrm_decode(new, 'le'), 'le').sections}
        assert set(b) - set(a) == {(9, 2782)} and set(a) <= set(b), rel
        for k, x in a.items():
            if b[k].data != x.data:
                assert k == (10, 20323) and struct.unpack_from('<I', x.data, 0x30)[0] == 2725 and struct.unpack_from('<I', b[k].data, 0x30)[0] == 2782, (rel, k)
                assert x.data[:0x30] == b[k].data[:0x30] and x.data[0x34:] == b[k].data[0x34:]
            assert (b[k].reloc, b[k].flags, b[k].ver, b[k].spec) == (x.reloc, x.flags, x.ver, x.spec), (rel, k)
        put(rel, new); print('  ', rel, '+lib 2782, mat 20323 +0x30 2725->2782', hashlib.md5(new).hexdigest()[:8])

if __name__ == '__main__':
    for a in sys.argv[1:]: print(a); globals()[a]()
