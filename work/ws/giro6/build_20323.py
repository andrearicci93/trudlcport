"""Task 3 (Giro 3) - costruzione OFFLINE dei DRM della baseline candidata B87 = B86_contratti + i 19 materiali trapiantati.
Per ogni materiale (stesso set di task3_run): regola di famiglia (mp_resolve + struct_resolve) -> f9m.build con SlotMapSpec (contratto sampler f14:
registro Xbox -> slot PC del materiale canonico) -> apply_virt -> bind_material -> legalize_consts -> controlli offline (lint, uninit, dcl, istr)
+ contract_gate f14 (>= 0.99 su ogni variante). Una ShaderLib DEDICATA per materiale (id nuovo libero), stessi byte in tutti i DRM che lo contengono.
Assemblaggio: come f12.assemble_phase ma sulla base work/baseline/B86_contratti/mods. Scrive SOLO in work/ws/codefirst/out_B87/.
Uso: build_B87.py [ONLY=id,id]  (env)"""
import sys, os, json, struct, collections, time, hashlib, pickle, glob
ROOT = '/path/to/trudlcport'
S4 = ROOT + '/work/ws/shader4'; CF = ROOT + '/work/ws/codefirst'; CT = ROOT + '/work/ws/contratti'
sys.path.insert(0, S4); sys.path.insert(0, CT); sys.path.insert(0, CF); sys.path.insert(0, ROOT + '/work/ws/giro5')
import f9m
import f14_slotmap as F14
import f4_build
import task3_run as T3
import mp_resolve, struct_resolve
from f12_build_all import *
import f12_build_all as F12

BASE = ROOT + '/work/ws/giro6/compose/mods'
OUTD = ROOT + '/work/ws/giro6/out_20323' + os.environ.get('OUTSUF', '')
_o = f9m.xsamp


def _xs(xblob, rb):
    if isinstance(rb, F14.SlotMapSpec): return F14._xsamp(xblob, rb)
    return _o(xblob, rb)


f9m.xsamp = _xs


def main():
    import texlib; texlib.set_baseline('B88b_acqua')
    ONLY = {int(x) for x in os.environ.get('ONLY', '').split(',') if x} or T3.FAM19
    L = libs(); D, DM, X, P = L['D'], L['DM'], L['X'], L['P']
    lit = {int(r['id_xbox']): r for r in __import__('csv').DictReader(open(S4 + '/illuminati.tsv'), delimiter='\t')}
    rev = collections.defaultdict(list)
    for x, p in x2p().items(): rev[p].append(x)
    occ, secs = material_occurrences(BASE, DM, lambda dl: dl in lit)
    # hash e id gia' occupati: tutto B45 + tutte le lib presenti in B86 + lib P/X/D
    taken, ids_used = f4_build.all_hashes()
    taken = set(taken); ids_used = set(ids_used)
    for rel, ss in secs.items():
        for (t, i), s in ss.items():
            if t == 9:
                ids_used.add(i)
                for e in shaderlib.parse(s.data, 'le')['entries'].values(): taken.add(bytes(e['hash']))
    free_ids = [i for i in range(2721, 9000) if i not in ids_used and i not in D and i not in P and i not in X]
    donor_cache = {}; plan = []; res = collections.OrderedDict(); t0 = time.time()
    for mid, items in sorted(occ.items()):
        if mid not in ONLY: continue
        dl = struct.unpack_from('>4I', DM[mid][0], 0x28)[2]
        why = None   # Giro 6: ricostruzione di una lib gia' trapiantata (pos2 = lib B84), nessun controllo sul surrogato originale
        if why: res[mid] = dict(status='escluso', why=why); print(mid, 'ESCLUSO', why, flush=True); continue
        s = canonical_material(items); pc = struct.unpack_from('<4I', s.data, 0x28)[2]
        if dl not in donor_cache:
            need = {k for k, x in enumerate(P[pc]['slots']) if x != 0xffffffff} if pc in P else set(range(8))
            pref = [(x, pc) for x in rev[pc]]; ok = None
            for cand in find_donors('D', dl, 0, want=12, prefer=pref):
                have = {k for k, x in enumerate(P[cand[1]]['slots']) if x != 0xffffffff}
                if not need <= have: continue
                r1 = find_donors('D', dl, 1, want=1, prefer=[cand])
                if r1 and r1[0] == cand: ok = cand; break
            donor_cache[dl] = ok
        dn = donor_cache[dl]
        if dn is None: res[mid] = dict(status='escluso', why='nessun donatore'); print(mid, 'nessun donatore', flush=True); continue
        if dn in T3.DONOR_OVERRIDE:
            alt = T3.DONOR_OVERRIDE[dn]
            have = {k for k, x in enumerate(P[alt[1]]['slots']) if x != 0xffffffff}; need = {k for k, x in enumerate(P[pc]['slots']) if x != 0xffffffff} if pc in P else set(range(8))
            if need <= have: dn = alt
        xs, pd = dn; bridge = material_pairs(xs, pd)
        mres, ties = mp_resolve.resolve(xs, pd)
        mres, ties, snotes = struct_resolve.apply(xs, pd, mres, ties)
        XPm = params(f9_common._Sec(*DM[mid]), 'be'); PPm = params(s, 'le')
        slotmap, rows = F14.derive_slotmap(mid, dl, s.data, s.reloc)
        mo = material_opts(mid); mo2 = dict(mo)
        if 'alpha1' in mo: mo2['alpha1'] = {slotmap[x] for x in mo['alpha1']}
        import texlib as _tl
        _dx = {slotmap[r['xbox_reg']] for r in rows if (_tl.xb_mean(r['xbox_tex']) or {}).get('kind') == 'DXN' and not any(c['name'].startswith('p_default_Normal') or '_Normal_' in c['name'] for c in XL.parse(D[dl]['entries'][D[dl]['slots'][0]]['blob']).ctab if c['set'] == 3 and c['reg'] == r['xbox_reg'])}
        if _dx and not os.environ.get('NODXN'): mo2['dxn'] = _dx; mo2['dxn_full'] = set(_dx); print('  dxn aggiunto sugli slot PC', sorted(_dx), flush=True)
        slots = [None] * 8; bad = None; info_m = dict(donor=list(dn), pareggi=len(ties), sampler_map=rows, virt=0, legal=0)
        for k, e in enumerate(P[pd]['slots']):
            if e == 0xffffffff: continue
            preg = {n: ri for n, rs, ri, rc in f9m.pc_ctab(P[pd]['entries'][e]['blob']) if rs == 3}
            spec = F14.SlotMapSpec(slotmap, preg)
            xblob = D[dl]['entries'][D[dl]['slots'][k & 1]]['blob']
            try:
                T, info = f9m.build(xblob, P[pd]['entries'][e]['blob'], X[xs]['entries'][X[xs]['slots'][k & 1]]['blob'], [(m_[2], m_[3]) for m_ in bridge],
                                    log=[], x_opts=mo2, x_samp_names=spec, mp_res=mres)
                for lane, cs in info['ties'].items():
                    vals = {round(float(XPm[c[0] - 100][c[1]]), 6) for c in cs if c[0] is not None and c[0] - 100 < len(XPm)}
                    if len(vals) > 1: raise f9m.Fail('pareggio non innocuo c%d.%s: %s' % (lane[0], 'xyzw'[lane[1]], sorted(vals)))
                T, vinfo = T3.apply_virt(T, info['virt'], XPm); info_m['virt'] += len(vinfo)
                T, binfo = bind_material(T, XPm, PPm)
                T, nleg = T3.legalize_consts(T); info_m['legal'] += nleg
                bc = sm3asm.encode(T)
                n, probs = F14.offline_checks(T, bc)
                used_new = set(slotmap.values()); engine = {r for nme, r in preg.items() if not nme.startswith('p_default')}
                coll = sorted(used_new & engine)
                if coll: probs.append('slot PC %s collidono coi sampler del donatore' % coll)
            except (f9m.Fail, Fail, xenos2sm3.Reject) as ex: bad = 'slot %d: %s' % (k, str(ex)[:160]); break
            except Exception as ex: bad = 'slot %d: ECCEZIONE %s' % (k, repr(ex)[:160]); break
            if probs: bad = 'slot %d: %s' % (k, probs); break
            slots[k] = bc
        if not bad:
            bcs = {k: b for k, b in enumerate(slots) if b is not None}
            mox = dict(mo)
            _dxr = {r['xbox_reg'] for r in rows if (_tl.xb_mean(r['xbox_tex']) or {}).get('kind') == 'DXN' and not any(c['name'].startswith('p_default_Normal') or '_Normal_' in c['name'] for c in XL.parse(D[dl]['entries'][D[dl]['slots'][0]]['blob']).ctab if c['set'] == 3 and c['reg'] == r['xbox_reg'])}
            if _dxr and not os.environ.get('NODXN'): mox['dxn'] = _dxr; mox['dxn_full'] = set(_dxr)
            g = F14.contract_gate(bcs, dl, rows, mox, XPm)
            info_m['gate'] = {k: round(v, 4) for k, v in g.items()}
            if min(g.values()) < F14.TH and not os.environ.get('NOGATE'): bad = 'gate di contratto %s' % info_m['gate']
        if bad:
            res[mid] = dict(status='escluso', why=bad, **info_m); print(mid, 'ESCLUSO', bad, flush=True); continue
        lid = free_ids.pop(0)
        for rel, _ in items: plan.append(dict(drm=rel, mat=mid, dlc=dl, old=pc, lib=lid, donor=dn, slots=slots, canon=s.data))
        res[mid] = dict(status='costruito', lib=lid, old=pc, drms=[r for r, _ in items], **info_m)
        print(mid, 'costruito lib', lid, 'old', pc, 'donatore', dn, 'gate min %.3f' % min(info_m['gate'].values()), 'virt', info_m['virt'], 'legal', info_m['legal'],
              '%.0fs' % (time.time() - t0), flush=True)
    os.makedirs(OUTD, exist_ok=True)
    pickle.dump(dict(plan=plan), open(OUTD + '/plan.pkl', 'wb'))
    # ---------------------------------------------------------------- assemblaggio (come f12.assemble_phase, base B86_contratti)
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
    json.dump(dict(materiali=res, drm=out), open(OUTD + '/B87_build.json', 'w'), indent=1, default=str)
    cnt = collections.Counter(r['status'] for r in res.values())
    print(dict(cnt), 'DRM scritti', len(out), 'lib nuove', sorted(libbytes), '%.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
