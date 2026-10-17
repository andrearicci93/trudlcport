"""F4 (rev. 2): traduce la lib Xbox 2173 adattandola al LAYOUT PARAMETRI PC dei materiali (MaterialParams non toccati) e costruisce B72.
- Il PS tradotto legge solo c100..c104 (i 5 vec4 che i 3 materiali PC forniscono) + globali; i valori Xbox non presenti nel blocco PC
  (P2.z, P5, P6, e P5.w che differisce fra materiali) diventano costanti `def` -> una lib per gruppo di materiali con gli stessi valori.
- Verifica numerica per materiale: PS con layout PC + params PC  ==  traduzione layout Xbox + params Xbox (1000 campioni).
- Normal map: sampler s2 = texture Xbox DXN -> PC DXT5 (y in alfa).
Uscita: work/ws/shader4/B72/dlc_caverns_hall.drm"""
import sys, os, struct, hashlib, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from f3_validate import *
import drm_write, drm_reloc as R, convert_dlc
import f4_lint

OLD_ID, XLIB = 1274, 2173
DRM = 'dlc_caverns_hall.drm'
SRC = os.path.join(ROOT, 'work/baseline/B45/mods', DRM)
BP = json.load(open(os.path.join(HERE, 'pc_ctab_by_pos.json')))
ALIAS = {'CameraPosition': 'g_CameraPosition', 'TimeVector': 'TimeVectorPS'}
DXN = 0x1a200171


def cfn(name, j, count):
    name = ALIAS.get(name, name); n = BP['2'].get(name)
    return None if n is None else n[0][0][0] + j


def all_hashes():
    import glob
    hs = set(); L = libs()
    for k in ('P', 'X', 'D'):
        for lid, lib in L[k].items():
            for e in lib['entries'].values(): hs.add(bytes(e['hash']))
    ids = set()
    for p in glob.glob(os.path.join(ROOT, 'work/baseline/B45/mods/**/*.drm'), recursive=True):
        try: d = drm_write.read(open(p, 'rb').read(), 'le')
        except Exception: continue
        for s in d.sections:
            if s.type == 9:
                ids.add(s.id)
                for e in shaderlib.parse(s.data, 'le')['entries'].values(): hs.add(bytes(e['hash']))
    return hs, ids


def make_hash(bc, taken):
    for salt in range(1000):
        h = hashlib.blake2b(b'TRU-DLC1-xenos2sm3|%d|' % salt + bc, digest_size=8).digest()
        if h not in taken and h != b'\0' * 8: return h
    raise RuntimeError('hash')


def build_lib(slot_bcs, taken):
    n = len(slot_bcs); tb = 4 * n
    body = bytearray(); offs = {}; slots = []; hs = []
    for bc in slot_bcs:
        if bc is None: slots.append(0xffffffff); continue
        if bc not in offs:
            h = make_hash(bc, taken); taken.add(h); hs.append(h.hex())
            offs[bc] = 8 + tb + len(body)
            body += struct.pack('<II', 0, 16 + len(bc)) + h + bc
        slots.append(offs[bc])
    out = bytearray(bytes([1, 0, 0, 0]) + struct.pack('<II', tb, 0) + struct.pack('<%dI' % n, *slots) + bytes(body))
    struct.pack_into('<I', out, 8, len(out) - 4)
    return bytes(out), hs


def params(rawsec, endian, n=None):
    e = '>' if endian == 'be' else '<'
    T = dict(R.parse(rawsec.reloc, endian).internal)[0x5C]
    n = struct.unpack_from(e + 'I', rawsec.data, 0x58)[0]
    f = struct.unpack_from(e + '%df' % (4 * n), rawsec.data, T)
    return [f[4 * i:4 * i + 4] for i in range(n)]


def main():
    L = libs(); D, P = L['D'], L['P']
    raw = open(SRC, 'rb').read(); d = drm_write.read(raw, 'le')
    pcs = {(s.type, s.id): s for s in d.sections}
    rawx, pk = convert_dlc.raw_dlc(DRM)
    xd = drm_write.read(rawx, 'be'); xs = {(s.type, s.id): s for s in xd.sections}
    fmt = {s.id: struct.unpack_from('>I', s.data, 4)[0] for s in xd.sections if s.type == 5}
    targets = sorted(mid for (t, mid), s in xs.items() if t == 10 and struct.unpack_from('>4I', s.data, 0x28)[2] == XLIB)
    XP = {m: params(xs[(10, m)], 'be') for m in targets}
    PP = {m: params(pcs[(10, m)], 'le') for m in targets}
    slotfmt = {}
    for m in targets:
        T = dict(R.parse(xs[(10, m)].reloc, 'be').internal)[0x54]
        ntex = xs[(10, m)].data[0x52]
        for k in range(ntex):
            tid, a, ty, fl, slot, filt = struct.unpack_from('>IIIBBH', xs[(10, m)].data, T + 16 * k)
            slotfmt.setdefault(m, {})[slot] = fmt.get(tid)
    dxn = {sl for sl in range(16) if all(slotfmt[m].get(sl) == DXN for m in targets)}
    print('materiali', targets, 'slot DXN', dxn)
    Dl = D[XLIB]
    blobs = [Dl['entries'][Dl['slots'][xs_]]['blob'] for xs_ in (0, 1)]
    # 1) quali componenti Xbox servono (pmap permissiva)
    perm = {(j, c): ('def', 0.0) for j in range(7) for c in range(4)}
    need = set()
    for b in blobs:
        t = xenos2sm3.Tr(b, cfn, samp=lambda n, c: c, opts={'pmap': perm, 'dxn': dxn}); t.run(); t.finish()
        for j, (r_, cs) in t.gather.items():
            for c in cs: need.add((j, c))
    print('componenti MaterialParams Xbox lette:', sorted(need))
    # 2) gruppi per valori non rappresentabili nel blocco PC
    def resolve(group):
        pm = {}; bad = []
        for (j, c) in sorted(need):
            xv = {XP[m][j][c] for m in group}
            cands = [(jj, cc) for jj in range(len(PP[group[0]])) for cc in range(4) if all(PP[m][jj][cc] == XP[m][j][c] for m in group)]
            if cands:
                cands.sort(key=lambda t: (t[0] != j or t[1] != c, t[1] != c, t))
                pm[(j, c)] = ('pc', cands[0][0], cands[0][1])
            elif len(xv) == 1: pm[(j, c)] = ('def', xv.pop())
            else: bad.append((j, c))
        return pm, bad
    sig = collections.defaultdict(list)
    for m in targets:
        key = tuple((j, c, XP[m][j][c]) for (j, c) in sorted(need) if not any(PP[m][jj][cc] == XP[m][j][c] for jj in range(len(PP[m])) for cc in range(4)) )
        sig[key].append(m)
    groups = list(sig.values())
    # una candidata PC puo' valere solo per un sottoinsieme: se resolve() non basta, divide ulteriormente
    final = []
    for g in groups:
        pm, bad = resolve(g)
        if not bad: final.append((g, pm)); continue
        for m in g:
            pm, bad = resolve([m]); assert not bad; final.append(([m], pm))
    hs_all, ids = all_hashes()
    free_ids = [i for i in range(2720, 3000) if i not in ids and i not in D and i not in P]
    assert XLIB not in ids and (XLIB not in P)
    gid = {}
    taken = set(hs_all)
    report = dict(groups=[], pcbase_hash_count=len(hs_all))
    new_secs = []
    tmpl = pcs[(9, OLD_ID)]
    for gi, (g, pm) in enumerate(final):
        lid = XLIB if gi == 0 else free_ids[gi - 1]
        outs = []
        for b in blobs:
            tr = xenos2sm3.translate(b, cfn, samp=lambda n, c: c, opts={'pmap': pm, 'dxn': dxn})
            bc = sm3asm.encode(tr.prog)
            errs = f4_lint.lint(bc, True)
            assert not errs, errs
            outs.append((tr, bc))
        # verifica numerica per materiale
        refs = [xenos2sm3.translate(b, cfn, samp=lambda n, c: c, opts={'dxn': dxn}) for b in blobs]
        for m in g:
            for si in (0, 1):
                cx = {100 + i: np.array(XP[m][i], np.float32) for i in range(7)}
                cp = {100 + i: np.array(PP[m][i], np.float32) for i in range(len(PP[m]))}
                # le costanti PC oltre il blocco fornito (c105+) sono NON fornite: usiamo valori casuali diversi per provare che non vengono lette
                rng = np.random.RandomState(5)
                for i in range(len(PP[m]), 8): cp[100 + i] = rng.uniform(5, 9, 4).astype(np.float32)
                r = compare(refs[si].prog, outs[si][0].prog, cvals=cx, cvalsB=cp)
                assert r['frac'] >= 0.999, (m, si, r['frac'])
                assert max(outs[si][0].consts) if outs[si][0].consts else True
                used = [x for x in r['usedB'] if 100 <= x <= 120]
                assert all(x <= 100 + len(PP[m]) - 1 for x in used), (m, used)
        slot_bcs = []
        for k, s in enumerate(P[OLD_ID]['slots']):
            slot_bcs.append(None if s == 0xffffffff else outs[k & 1][1])
        sec, hs = build_lib(slot_bcs, taken)
        # riparse
        lib = shaderlib.parse(sec, 'le')
        for k, s in enumerate(lib['slots']):
            if s == 0xffffffff: continue
            b = lib['entries'][s]['blob']; assert b[:sm3dis.bytecode_len(b)] == slot_bcs[k]
        new_secs.append(drm_write.Section(9, lid, sec, b'', flags=tmpl.flags, ver=tmpl.ver, spec=tmpl.spec, pad=tmpl.pad))
        for m in g: gid[m] = lid
        report['groups'].append(dict(lib_id=lid, materiali=g, hash=hs, ninstr=[o[0].ninstr for o in outs],
                                     consts=sorted(set(r_ for o in outs for r_ in o[0].consts)),
                                     inline_params={('P%d.%s' % (j, 'xyzw'[c])): v[1] for (j, c), v in pm.items() if v[0] == 'def'},
                                     pc_params={('P%d.%s' % (j, 'xyzw'[c])): ('P%d.%s' % (v[1], 'xyzw'[v[2]])) for (j, c), v in pm.items() if v[0] == 'pc'},
                                     notes=outs[0][0].notes, tex_dxn=sorted(dxn)))
        print('gruppo lib', lid, 'materiali', g, 'istruzioni', [o[0].ninstr for o in outs], 'consts', report['groups'][-1]['consts'])
        print('   inline:', report['groups'][-1]['inline_params'])
    # DRM
    d2 = drm_write.read(raw, 'le'); secs = list(d2.sections)
    i_old = [(s.type, s.id) for s in secs].index((9, OLD_ID))
    for k, ns in enumerate(new_secs): secs.insert(i_old + 1 + k, ns)
    for s in secs:
        if s.type == 10 and s.id in gid:
            data = bytearray(s.data); assert struct.unpack_from('<I', data, 0x30)[0] == OLD_ID
            struct.pack_into('<I', data, 0x30, gid[s.id]); s.data = bytes(data)
    d2.sections = secs
    out_raw = d2.write('le'); d3 = drm_write.read(out_raw, 'le')
    a = {(s.type, s.id): s for s in drm_write.read(raw, 'le').sections}; b = {(s.type, s.id): s for s in d3.sections}
    assert set(b) - set(a) == {(9, g_['lib_id']) for g_ in report['groups']} and set(a) <= set(b)
    changed = []
    for key, s in a.items():
        t = b[key]
        assert (t.reloc, t.flags, t.ver, t.spec, t.pad) == (s.reloc, s.flags, s.ver, s.spec, s.pad), key
        if t.data != s.data:
            changed.append(key); assert key[0] == 10 and key[1] in gid
            diff = [i for i in range(len(s.data)) if s.data[i] != t.data[i]]
            assert len(s.data) == len(t.data) and all(0x30 <= i < 0x34 for i in diff), (key, diff)
    assert sorted(changed) == sorted((10, m) for m in gid)
    # nessun target 'external' verso indici >= primo indice tipo 9 (le lib si referenziano per id)
    first9 = min(i for i, s in enumerate(d.sections) if s.type == 9)
    mx = max((si for s in d.sections for si, _, _ in R.parse(s.reloc, 'le').external), default=-1)
    assert mx < first9, (mx, first9)
    od = os.path.join(HERE, 'B72'); os.makedirs(od, exist_ok=True)
    enc = drm_write.cdrm_encode(out_raw, 'le'); open(os.path.join(od, DRM), 'wb').write(enc)
    report['md5'] = hashlib.md5(enc).hexdigest(); report['size'] = len(enc); report['changed'] = [list(k) for k in changed]
    report['max_external_target_index'] = mx; report['first_type9_index'] = first9
    json.dump(report, open(os.path.join(HERE, 'f4_build_B72.json'), 'w'), indent=1, default=str)
    print('B72 scritto', report['size'], report['md5'], 'cambiati', changed)


if __name__ == '__main__':
    main()
