"""Giro 5 - cantieri 2b/3a: traduzione DIRETTA (f13) dei PS DLC NON illuminati con surrogato PC scadente (acqua/cascata/vetrata),
con il CONTRATTO SAMPLER f14 (registro Xbox -> slot PC del materiale canonico) che f13_unlit non applicava (sampler = stesso registro).
Base: work/baseline/B87_materiali19/mods. Una lib DEDICATA per materiale (id nuovo libero), stessi byte in tutti i DRM che lo contengono.
Controlli offline per variante: lint, letture non inizializzate, dcl, istruzioni, sampler <= s15, collisioni slot/sampler motore,
gate di contratto f14 (entry_equivalence) e interfaccia VS->PS. Scrive SOLO in work/ws/giro5/out_unlit/.
Uso: build_unlit.py [probe|build]   env LIBS=2090,2164,... (default: 2090,2164,2177,2202,2205)"""
import sys, os, json, struct, collections, time, hashlib, pickle
ROOT = '/path/to/trudlcport'
S4 = ROOT + '/work/ws/shader4'; CF = ROOT + '/work/ws/codefirst'; CT = ROOT + '/work/ws/contratti'
sys.path.insert(0, S4); sys.path.insert(0, CT); sys.path.insert(0, CF)
import f14_slotmap as F14
import f4_build
import f13_unlit as F13
from f13_unlit import *            # Consts, bind_material, params, material_opts, ... (via f12/f10/f9)
import task3_run as T3
sys.path.insert(0, ROOT + '/work/ws/giro5')
import texlib
texlib.set_baseline('B87_materiali19')

BASE = ROOT + '/work/baseline/B87_materiali19/mods'
OUTD = ROOT + '/work/ws/giro5/out_unlit'
LIBS = [int(x) for x in os.environ.get('LIBS', '2090,2164,2177,2202,2205').split(',') if x]


def translate_unlit_slot(xblob, opts, slotmap):
    """Come f13.translate_unlit ma i sampler del materiale (p_default*) vanno sullo SLOT PC dell'entry; gli altri tengono il registro Xbox."""
    K = Consts([])
    names = {c['reg']: c['name'] for c in XL.parse(xblob).ctab if c['set'] == 3}
    def samp(name, c):
        n = names.get(c, name)
        return slotmap.get(c, c) if n.startswith('p_default') else c
    t = xenos2sm3.translate(xblob, K.fn, bools=None, samp=samp, opts=dict(opts or {}))
    if K.extra: raise Fail('costanti senza registro PC: %s' % sorted({k[0] for k in K.extra}))
    return sm3asm.parse_text(t.text)


def vs_ps_interface(vs_bc, ps_prog):
    """Texcoord scritti dal VS PC (dcl output) vs letti dal PS: -> (mancanti nel VS, extra nel VS)."""
    vs = decode_pc(vs_bc)
    outs = set()
    for i in vs.instrs():
        if i.op == 'dcl' and i.ops[0].rtype in (sm3asm.RT_TEXOUT, sm3asm.RT_ATTR):
            outs.add((i.usage & 0x1f, (i.usage >> 16) & 15))
    ins = set()
    for i in ps_prog.instrs():
        if i.op == 'dcl' and i.ops[0].rtype == sm3asm.RT_INPUT: ins.add((i.usage & 0x1f, (i.usage >> 16) & 15))
    return sorted(ins - outs), sorted(outs - ins)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'probe'
    L = libs(); D, DM, X, P = L['D'], L['DM'], L['X'], L['P']
    occ, secs = material_occurrences(BASE, DM, lambda dl: dl in LIBS)
    taken, ids_used = f4_build.all_hashes(); taken = set(taken); ids_used = set(ids_used)
    for rel, ss in secs.items():
        for (t, i), s in ss.items():
            if t == 9:
                ids_used.add(i)
                for e in shaderlib.parse(s.data, 'le')['entries'].values(): taken.add(bytes(e['hash']))
    free_ids = [i for i in range(2775, 9000) if i not in ids_used and i not in D and i not in P and i not in X]
    plan = []; res = collections.OrderedDict(); t0 = time.time()
    for mid, items in sorted(occ.items()):
        dl = struct.unpack_from('>4I', DM[mid][0], 0x28)[2]
        why = shared_problem(dl, items, secs)
        if why: res[mid] = dict(status='escluso', why=why); print(mid, 'ESCLUSO', why, flush=True); continue
        s = canonical_material(items); pc = struct.unpack_from('<4I', s.data, 0x28)[2]
        vs_lib = struct.unpack_from('<4I', s.data, 0x28)[3]
        slotmap, rows = F14.derive_slotmap(mid, dl, s.data, s.reloc)
        occs = [k for k, x in enumerate(P[pc]['slots']) if x != 0xffffffff] if pc in P else [0, 1]
        XPm = params(f9_common._Sec(*DM[mid]), 'be'); PPm = params(s, 'le')
        mo = material_opts(mid); mo2 = dict(mo)
        if 'alpha1' in mo: mo2['alpha1'] = {slotmap[x] for x in mo['alpha1']}
        # DXN Xbox -> DXT5 PC (R=x, G=1, B=0, A=y): y da alfa anche se il sampler non si chiama *_Normal_ (formato reale della texture Xbox)
        dxn = {slotmap[r['xbox_reg']] for r in rows if (texlib.xb_mean(r['xbox_tex']) or {}).get('kind') == 'DXN'}
        if dxn: mo2['dxn'] = dxn
        slots = [None] * (len(P[pc]['slots']) if pc in P else 2); bad = None; info_m = dict(dxn=sorted(dxn), sampler_map=rows, vs_lib=vs_lib, occs=occs, gate={}, istr={}, iface={})
        for k in occs:
            xblob = D[dl]['entries'][D[dl]['slots'][k & 1]]['blob']
            try:
                T = translate_unlit_slot(xblob, mo2, slotmap)
                T, binfo = bind_material(T, XPm, PPm)
                T, nleg = T3.legalize_consts(T)
                bc = sm3asm.encode(T)
                n, probs = F14.offline_checks(T, bc)
                engine = {c['reg'] for c in XL.parse(xblob).ctab if c['set'] == 3 and not c['name'].startswith('p_default')}
                coll = sorted(set(slotmap.values()) & engine)
                if coll: probs.append('slot PC %s collidono coi sampler motore' % coll)
                info_m['istr'][k] = n
                if vs_lib in P:
                    cov = 0; tot = 0; best = None
                    for off in sorted(set(P[vs_lib]['slots']) - {0xffffffff}):
                        miss, extra = vs_ps_interface(P[vs_lib]['entries'][off]['blob'], T); tot += 1
                        if not miss: cov += 1
                        if best is None or len(miss) < len(best): best = miss
                    info_m['iface'][k] = dict(vs_che_coprono=cov, vs_totali=tot, miglior_mancante=best)
                    if cov == 0: probs.append('nessun VS PC della lib %d scrive tutti gli ingressi del PS (manca %s)' % (vs_lib, best))
            except (Fail, xenos2sm3.Reject) as ex: bad = 'slot %d: %s' % (k, str(ex)[:200]); break
            except Exception as ex: bad = 'slot %d: ECCEZIONE %s' % (k, repr(ex)[:200]); break
            if probs: bad = 'slot %d: %s' % (k, probs); break
            slots[k] = bc
        if not bad:
            bcs = {k: b for k, b in enumerate(slots) if b is not None}
            mox = dict(mo)
            dx = {r['xbox_reg'] for r in rows if (texlib.xb_mean(r['xbox_tex']) or {}).get('kind') == 'DXN'}
            if dx: mox['dxn'] = dx
            g = F14.contract_gate(bcs, dl, rows, mox, XPm)
            info_m['gate'] = {k: round(v, 4) for k, v in g.items()}
            if min(g.values()) < F14.TH: bad = 'gate di contratto %s' % info_m['gate']
        if bad: res[mid] = dict(status='escluso', why=bad, **info_m); print(mid, 'lib', dl, 'ESCLUSO', bad, flush=True); continue
        lid = free_ids.pop(0)
        for rel, _ in items: plan.append(dict(drm=rel, mat=mid, dlc=dl, old=pc, lib=lid, slots=slots, canon=s.data))
        res[mid] = dict(status='costruito', lib=lid, old=pc, xlib=dl, drms=[r for r, _ in items], **info_m)
        print(mid, 'lib', dl, 'costruito ->', lid, 'old', pc, 'gate', info_m['gate'], 'istr', info_m['istr'], 'iface', info_m['iface'], '%.0fs' % (time.time() - t0), flush=True)
    if mode == 'probe': return
    os.makedirs(OUTD, exist_ok=True)
    pickle.dump(dict(plan=plan), open(OUTD + '/plan.pkl', 'wb'))
    by_drm = collections.defaultdict(list)
    for it in plan: by_drm[it['drm']].append(it)
    libbytes = {}; out = {}
    for rel, items in sorted(by_drm.items()):
        raw = open(os.path.join(BASE, rel), 'rb').read(); d = drm_write.read(raw, 'le'); ss = list(d.sections)
        for it in items:
            if it['lib'] not in libbytes: libbytes[it['lib']] = f4_build.build_lib(it['slots'], taken)[0]
            tmpl = next(x for x in ss if x.type == 9 and x.id == it['old'])
            ss.insert(ss.index(tmpl) + 1, drm_write.Section(9, it['lib'], libbytes[it['lib']], b'', flags=tmpl.flags, ver=tmpl.ver, spec=tmpl.spec, pad=tmpl.pad))
            m = next(x for x in ss if x.type == 10 and x.id == it['mat'])
            assert struct.unpack_from('<I', m.data, 0x30)[0] == it['old'] and len(m.data) == len(it['canon'])
            data_ = bytearray(it['canon']); struct.pack_into('<I', data_, 0x30, it['lib']); m.data = bytes(data_)
        d.sections = ss; out_raw = d.write('le')
        a = {(x.type, x.id): x for x in drm_write.read(raw, 'le').sections}; b = {(x.type, x.id): x for x in drm_write.read(out_raw, 'le').sections}
        assert set(b) - set(a) == {(9, it['lib']) for it in items} and set(a) <= set(b), rel
        mats = {it['mat']: it for it in items}
        for key, x in a.items():
            t = b[key]
            assert (t.reloc, t.flags, t.ver, t.spec, t.pad) == (x.reloc, x.flags, x.ver, x.spec, x.pad), (rel, key)
            if t.data != x.data:
                assert key[0] == 10 and key[1] in mats, (rel, key)
                want = bytearray(mats[key[1]]['canon']); struct.pack_into('<I', want, 0x30, mats[key[1]]['lib'])
                assert t.data == bytes(want), (rel, key)
        first9 = min(i for i, x in enumerate(drm_write.read(raw, 'le').sections) if x.type == 9)
        mx = max((si for x in drm_write.read(raw, 'le').sections for si, _, _ in R.parse(x.reloc, 'le').external), default=-1)
        assert mx < first9, (rel, mx, first9)
        enc = drm_write.cdrm_encode(out_raw, 'le')
        p = os.path.join(OUTD, 'mods', rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'wb').write(enc)
        out[rel] = dict(materiali=sorted(mats), md5=hashlib.md5(enc).hexdigest(), size=len(enc))
        print('scritto', rel, 'materiali', sorted(mats), flush=True)
    # bytecode per vm_ps_validate/vm_ps_draw (da eseguire in VM quando l'utente decide)
    vd = OUTD + '/valid'; os.makedirs(vd, exist_ok=True)
    for it in plan:
        for k, b in enumerate(it['slots']):
            if b is not None: open(vd + '/lib%d_s%d.bin' % (it['lib'], k), 'wb').write(b)
    json.dump(dict(materiali=res, drm=out), open(OUTD + '/build.json', 'w'), indent=1, default=str)
    print(dict(collections.Counter(r['status'] for r in res.values())), 'DRM scritti', len(out), 'lib nuove', sorted(libbytes), '%.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
