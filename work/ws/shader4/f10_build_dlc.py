"""F10 - costruisce le lib DLC trapiantate (f9) e la baseline candidata.
Per ogni lib DLC illuminata con donatore equivalente: 8 slot PC (slot k = X slot k&1 + catena luci del donatore slot k), parametri
materiale: registro PC se il valore coincide con quello Xbox nella stessa posizione, altrimenti costante interna (def) col valore Xbox
(la lib e' usata da un solo materiale). Controlli offline per slot:
  - istruzioni <= 512; lint del bytecode (f4_lint);
  - LUCI SPENTE: T (bool PC tutti falsi) == traduzione diretta Xbox di X con LightEnabled=0 (superficie, ambiente, nebbia);
  - DRM: solo nuove sezioni tipo 9 + 4 byte (pos2) dei materiali interessati.
uso: tools/venv/bin/python -I work/ws/shader4/f10_build_dlc.py [id_dlc ...]   (default 2244 2264)
uscita: work/ws/shader4/B75/<drm> + f10_build.json"""
import sys, os, json, hashlib, struct, collections, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from f9_transplant import *
import f9_common
from f4_build import params, build_lib, all_hashes, make_hash
import drm_write, f4_lint, drm_reloc as R

SRC = os.path.join(ROOT, 'work/baseline/B73/mods')
OUT = os.path.join(HERE, 'B77')


def bind_material(prog, XP, PP):
    """letture c100+j: se il vec4 Xbox == PC (componenti lette) resta il registro PC, altrimenti def col valore Xbox."""
    B = body(prog); st = stypes(prog)
    used = collections.defaultdict(set)
    for i in B:
        for j, o in enumerate(i.ops):
            if not o.isdst and o.rtype == sm3asm.RT_CONST and 100 <= o.num < 100 + 16:
                for c in lanes(i, j, st): used[o.num - 100].add(c)
    defs = {i.ops[0].num for i in header(prog) if i.op == 'def'}
    taken = {o.num for i in prog.instrs() for o in i.ops if o.rtype == sm3asm.RT_CONST} | defs
    free = [r for r in range(223, 0, -1) if r not in taken and not 100 <= r < 116]
    remap = {}; newdefs = []; info = {}
    for j, cs in sorted(used.items()):
        if j >= len(XP): raise Fail('MaterialParams[%d] letto ma il materiale Xbox ne ha %d' % (j, len(XP)))
        same = j < len(PP) and all(abs(XP[j][c] - PP[j][c]) < 1e-6 for c in cs)
        if same: info[j] = 'PC'; continue
        r = free.pop(0); remap[100 + j] = r; info[j] = 'def c%d' % r
        newdefs.append(sm3asm.parse_text('ps_3_0\ndef c%d, %s\n' % (r, ', '.join('%.9g' % v for v in XP[j]))).instrs()[0])
    for i in B:
        for o in i.ops:
            if not o.isdst and o.rtype == sm3asm.RT_CONST and o.num in remap: o.num = remap[o.num]
    return sm3asm.Program(prog.kind, prog.major, prog.minor, header(prog) + newdefs + B), info


def lights_off_check(progT, xblob, XP, seed=11, opts=None):
    """T con bool PC falsi vs traduzione diretta di X con luci Xbox spente (stessi nomi di costante -> stessi registri)."""
    pct = []
    K = Consts(pct)
    sh = XL.parse(xblob); bn = bool_names(sh)
    bools = {i: 0 for i in bn}
    o = dict(opts or {}); o['noopt'] = True
    t = xenos2sm3.translate(xblob, K.fn, bools=bools, samp=lambda n, c: c, opts=o)
    progX = sm3asm.parse_text(t.text)
    env = Env(seed, XP)
    a = env.run(progT, body(progT), env.state0(progT), {})
    b = env.run(progX, body(progX), env.state0(progX), {})
    ca, cb = a[0].get((sm3asm.RT_COLOROUT, 0)), b[0].get((sm3asm.RT_COLOROUT, 0))
    if ca is None or cb is None: return 0.0
    return float((np.isclose(ca, cb, **TOL).all(axis=1) & (a[1] == b[1]) | (a[1] & b[1])).mean())


def main():
    ids = [int(a) for a in sys.argv[1:]] or [2244, 2264]
    L = libs(); D, DM, X, P = L['D'], L['DM'], L['X'], L['P']
    rows = {int(r['id_xbox']): r for r in csv.DictReader(open(os.path.join(HERE, 'illuminati.tsv')), delimiter='\t')}
    rev = collections.defaultdict(list)
    for x, p in x2p().items(): rev[p].append(x)
    hs_all, ids_used = all_hashes(); taken = set(hs_all)
    free_ids = [i for i in range(2721, 4000) if i not in ids_used and i not in D and i not in P and i not in X]
    report = {'libs': []}
    per_drm = collections.defaultdict(list)
    for dl in ids:
        r = rows[dl]; pc = int(r['id_pc_surrogato']); drm = r['drm'].split(',')[0]
        mats = [m for m, (d, rr) in DM.items() if struct.unpack_from('>4I', d, 0x28)[2] == dl]
        pref = [(x, pc) for x in rev[pc]]
        donors = []
        need = {k for k, x in enumerate(P[pc]['slots']) if x != 0xffffffff}      # varianti usate dal surrogato attuale
        for cand in find_donors('D', dl, 0, want=12, prefer=pref):
            have = {k for k, x in enumerate(P[cand[1]]['slots']) if x != 0xffffffff}
            if not need <= have: print('  donatore %s scartato: varianti %s, servono %s' % (cand, sorted(have), sorted(need))); continue
            if find_donors('D', dl, 1, want=1, prefer=[cand]) and find_donors('D', dl, 1, want=1, prefer=[cand])[0] == cand: donors.append(cand)
        if not donors: print(dl, 'nessun donatore valido per entrambi gli slot Xbox'); continue
        xs, pd = donors[0]
        bridge = material_pairs(xs, pd)
        print('lib', dl, drm, 'materiali', mats, 'donatore Xs %d / Pd %d (alternative %s)' % (xs, pd, donors[1:]))
        # parametri del materiale: Xbox originali e PC attuali (B73)
        d = drm_write.read(open(os.path.join(SRC, drm), 'rb').read(), 'le'); sec = {(s.type, s.id): s for s in d.sections}
        assert len(mats) == 1, mats
        XPm = params(f9_common._Sec(*DM[mats[0]]), 'be'); PPm = params(sec[(10, mats[0])], 'le')
        slot_bcs = []; slot_info = []
        for k, s in enumerate(P[pd]['slots']):
            if s == 0xffffffff: slot_bcs.append(None); continue
            log = []
            xblob = D[dl]['entries'][D[dl]['slots'][k & 1]]['blob']
            T, info = build(xblob, P[pd]['entries'][s]['blob'], X[xs]['entries'][X[xs]['slots'][k & 1]]['blob'], [(m_[2], m_[3]) for m_ in bridge], x_samp_names=None, log=log)
            T, binfo = bind_material(T, XPm, PPm)
            n = len(body(T))
            off = lights_off_check(T, xblob, XPm)
            bc = sm3asm.encode(T); errs = f4_lint.lint(bc, True)
            ok = n <= 512 and not errs and off >= 0.99
            slot_info.append(dict(slot=k, istr=n, luci_spente=off, lint=errs[:3], parametri=binfo, log=log, ok=ok))
            print('  slot %d: istr %d, luci spente %.3f, lint %s, parametri %s %s' % (k, n, off, 'ok' if not errs else errs[:2], binfo, '' if ok else '<< NON OK'))
            if not ok: raise SystemExit('slot %d non valido: stop' % k)
            slot_bcs.append(bc)
        sec_bytes, hs = build_lib(slot_bcs, taken)
        lib = shaderlib.parse(sec_bytes, 'le')
        for k, s in enumerate(lib['slots']):
            if s == 0xffffffff: continue
            b = lib['entries'][s]['blob']; assert b[:sm3dis.bytecode_len(b)] == slot_bcs[k]
        lid = free_ids.pop(0)
        per_drm[drm].append(dict(lib_id=lid, sec=sec_bytes, mats=mats, old=pc))
        report['libs'].append(dict(dlc=dl, drm=drm, lib_id=lid, donatore=[xs, pd], materiali=mats, hash=hs, slot=slot_info))
    os.makedirs(OUT, exist_ok=True)
    for drm, items in per_drm.items():
        raw = open(os.path.join(SRC, drm), 'rb').read(); d = drm_write.read(raw, 'le'); secs = list(d.sections)
        for it in items:
            tmpl = next(s for s in secs if s.type == 9 and s.id == it['old'])
            i_old = secs.index(tmpl)
            secs.insert(i_old + 1, drm_write.Section(9, it['lib_id'], it['sec'], b'', flags=tmpl.flags, ver=tmpl.ver, spec=tmpl.spec, pad=tmpl.pad))
            for s in secs:
                if s.type == 10 and s.id in it['mats']:
                    data = bytearray(s.data); assert struct.unpack_from('<I', data, 0x30)[0] == it['old'], (s.id, struct.unpack_from('<4I', data, 0x28))
                    struct.pack_into('<I', data, 0x30, it['lib_id']); s.data = bytes(data)
        d.sections = secs; out_raw = d.write('le')
        a = {(s.type, s.id): s for s in drm_write.read(raw, 'le').sections}; b = {(s.type, s.id): s for s in drm_write.read(out_raw, 'le').sections}
        assert set(b) - set(a) == {(9, it['lib_id']) for it in items} and set(a) <= set(b)
        for key, s in a.items():
            t = b[key]
            assert (t.reloc, t.flags, t.ver, t.spec, t.pad) == (s.reloc, s.flags, s.ver, s.spec, s.pad), key
            if t.data != s.data:
                assert key[0] == 10 and any(key[1] in it['mats'] for it in items), key
                diff = [i for i in range(len(s.data)) if s.data[i] != t.data[i]]
                assert len(s.data) == len(t.data) and all(0x30 <= i < 0x34 for i in diff), (key, diff)
        first9 = min(i for i, s in enumerate(drm_write.read(raw, 'le').sections) if s.type == 9)
        mx = max((si for s in drm_write.read(raw, 'le').sections for si, _, _ in R.parse(s.reloc, 'le').external), default=-1)
        assert mx < first9, (mx, first9)
        enc = drm_write.cdrm_encode(out_raw, 'le'); open(os.path.join(OUT, drm), 'wb').write(enc)
        report.setdefault('drm', {})[drm] = dict(size=len(enc), md5=hashlib.md5(enc).hexdigest())
        print('scritto', drm, len(enc), hashlib.md5(enc).hexdigest())
    json.dump(report, open(os.path.join(HERE, 'f10_build.json'), 'w'), indent=1, default=str)


if __name__ == '__main__':
    main()
