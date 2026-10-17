"""F13 - shader DLC SENZA luci con surrogato PC scadente: traduzione diretta Xenos->SM3 (come B72), per materiale.
Costanti per nome (tabella PC globale + alias), sampler = stesso registro (slot di texture del materiale), MaterialParams col valore Xbox
dove il PC differisce (bind_material), alfa 6610 come f12. Varianti: slot PC k <- slot Xbox k&1, occupazione del surrogato attuale.
uso: python f13_unlit.py build ID_LIB_XBOX [...]   -> valid_unlit/*.bin + f13_plan.pkl   (poi vm_ps_draw.ps1 su valid_unlit)
     python f13_unlit.py assemble BASE OUT          -> work/ws/shader4/<OUT>/ con le lib validate, partendo da work/baseline/<BASE>/mods"""
import sys, os, glob, pickle, struct, collections, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from f12_build_all import *

VALU = os.path.join(HERE, 'valid_unlit'); PLANU = os.path.join(HERE, 'f13_plan.pkl')


def translate_unlit(xblob, opts):
    K = Consts([])
    t = xenos2sm3.translate(xblob, K.fn, bools=None, samp=lambda n, c: c, opts=dict(opts or {}))
    if K.extra: raise Fail('costanti senza registro PC: %s' % sorted({k[0] for k in K.extra}))
    return sm3asm.parse_text(t.text)


def build_phase(ids, base='B83'):
    src = os.path.join(ROOT, 'work/baseline', base, 'mods')
    L = libs(); D, DM, P = L['D'], L['DM'], L['P']
    hs_all, ids_used = all_hashes(); used_ids = set(ids_used) | set(D) | set(P) | set(L['X'])
    for path in glob.glob(os.path.join(src, '**', '*.drm'), recursive=True):
        try: used_ids |= {s.id for s in drm_write.read(open(path, 'rb').read(), 'le').sections if s.type == 9}
        except Exception: pass
    free_ids = [i for i in range(3000, 9000) if i not in used_ids]
    os.makedirs(VALU, exist_ok=True)
    for f in glob.glob(os.path.join(VALU, '*.bin')): os.remove(f)
    plan = []
    occ, secs = material_occurrences(src, DM, lambda dl: dl in ids)
    for mid, items in sorted(occ.items()):
        dl = struct.unpack_from('>4I', DM[mid][0], 0x28)[2]
        why = shared_problem(dl, items, secs)
        if why: print('mat', mid, 'lib', dl, 'ESCLUSO', why); continue
        s = canonical_material(items); pc = struct.unpack_from('<4I', s.data, 0x28)[2]
        occs = [k for k, x in enumerate(P[pc]['slots']) if x != 0xffffffff] if pc in P else [0, 1]
        XPm = params(f9_common._Sec(*DM[mid]), 'be'); PPm = params(s, 'le'); mo = material_opts(mid)
        slots = [None] * (len(P[pc]['slots']) if pc in P else 2)
        try:
            for k in occs:
                xb = D[dl]['entries'][D[dl]['slots'][k & 1]]['blob']
                T, binfo = bind_material(translate_unlit(xb, mo), XPm, PPm)
                bc = sm3asm.encode(T); errs = f4_lint.lint(bc, True)
                if errs or uninit_reads(T) or decl_problems(T): raise Fail('controlli statici: %s' % (errs[:2] or 'uninit/dcl'))
                slots[k] = bc
        except (Fail, xenos2sm3.Reject) as e:
            print('mat', mid, 'lib', dl, 'ESCLUSO', e); continue
        lid = free_ids.pop(0)   # UNA lib per materiale, uguale in tutti i DRM che lo contengono
        for k, bc in enumerate(slots):
            if bc is not None: open(os.path.join(VALU, 'lib%d_s%d.bin' % (lid, k)), 'wb').write(bc)
        for rel, _ in items: plan.append(dict(drm=rel, mat=mid, dlc=dl, old=pc, lib=lid, slots=slots, canon=s.data))
        print('mat', mid, 'lib', dl, '->', lid, 'slot', [k for k, b in enumerate(slots) if b is not None], 'in', len(items), 'DRM')
    pickle.dump(dict(plan=plan, base=base), open(PLANU, 'wb'))


def assemble_phase(base, outname):
    data = pickle.load(open(PLANU, 'rb')); plan = data['plan']; src = os.path.join(ROOT, 'work/baseline', base, 'mods')
    res = {}
    for line in open(os.path.join(VALU, 'draw_result.txt'), encoding='ascii', errors='replace'):
        if '`t' in line or '\t' in line:
            name, r = line.replace('`t', '\t').split('\t', 1); res[name.strip()] = all(v.endswith('0x00000000') for v in r.split())
    hs_all, _ = all_hashes(); taken = set(hs_all); outd = os.path.join(HERE, outname)
    by = collections.defaultdict(list)
    for it in plan:
        names = ['lib%d_s%d.bin' % (it['lib'], k) for k, b in enumerate(it['slots']) if b is not None]
        if all(res.get(n) for n in names): by[it['drm']].append(it)
        else: print('scartata dalla VM', it['drm'], it['mat'], it['lib'])
    libbytes = {}
    for rel, items in by.items():
        raw = open(os.path.join(src, rel), 'rb').read(); d = drm_write.read(raw, 'le'); secs = list(d.sections)
        for it in items:
            if it['lib'] not in libbytes: libbytes[it['lib']] = build_lib(it['slots'], taken)[0]   # stessi byte in ogni DRM
            sec_bytes = libbytes[it['lib']]
            tmpl = next(s for s in secs if s.type == 9 and s.id == it['old'])
            secs.insert(secs.index(tmpl) + 1, drm_write.Section(9, it['lib'], sec_bytes, b'', flags=tmpl.flags, ver=tmpl.ver, spec=tmpl.spec, pad=tmpl.pad))
            m = next(s for s in secs if s.type == 10 and s.id == it['mat'])
            assert struct.unpack_from('<I', m.data, 0x30)[0] == it['old'] and len(m.data) == len(it['canon'])
            b_ = bytearray(it['canon']); struct.pack_into('<I', b_, 0x30, it['lib']); m.data = bytes(b_)
        d.sections = secs; out_raw = d.write('le')
        a = {(s.type, s.id): s for s in drm_write.read(raw, 'le').sections}; b = {(s.type, s.id): s for s in drm_write.read(out_raw, 'le').sections}
        assert set(b) - set(a) == {(9, it['lib']) for it in items} and set(a) <= set(b)
        for key, s in a.items():
            if b[key].data != s.data:
                assert key[0] == 10 and key[1] in {it['mat'] for it in items}, key
                it = next(i for i in items if i['mat'] == key[1]); want = bytearray(it['canon']); struct.pack_into('<I', want, 0x30, it['lib'])
                assert b[key].data == bytes(want), key
        enc = drm_write.cdrm_encode(out_raw, 'le'); os.makedirs(os.path.dirname(os.path.join(outd, rel)), exist_ok=True)
        open(os.path.join(outd, rel), 'wb').write(enc); print('scritto', rel, len(items), hashlib.md5(enc).hexdigest())


if __name__ == '__main__':
    if sys.argv[1] == 'build': build_phase([int(a) for a in sys.argv[2:]])
    else: assemble_phase(sys.argv[2], sys.argv[3])
