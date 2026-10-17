"""Passo 2 (Giro 4): valutazione statica dei 5 esclusi con la pipeline attuale (f9m + SlotMapSpec + legalize con temp morti), SENZA shared_problem e SENZA scrivere nulla.
Per ogni materiale: copie (DRM, md5), donatore trovato, esito build per variante (costruito/errore), gate di contratto."""
import sys, os, struct, collections, hashlib
ROOT = '/path/to/trudlcport'
sys.path[:0] = [ROOT + '/work/ws/shader4', ROOT + '/work/ws/contratti', ROOT + '/work/ws/codefirst']
import f9m, f14_slotmap as F14, task3_run as T3, mp_resolve, struct_resolve
from f12_build_all import *
import build_B87 as B   # patcha f9m.xsamp
MIDS = [int(x) for x in os.environ.get('ONLY', '20262,21164,20345,21118,24275').split(',')]
L = libs(); D, DM, X, P = L['D'], L['DM'], L['X'], L['P']
lit = {int(r['id_xbox']): r for r in __import__('csv').DictReader(open(ROOT + '/work/ws/shader4/illuminati.tsv'), delimiter='\t')}
rev = collections.defaultdict(list)
for x, p in x2p().items(): rev[p].append(x)
occ, secs = material_occurrences(B.BASE, DM, lambda dl: dl in lit)
for mid in MIDS:
    items = occ.get(mid, [])
    dl = struct.unpack_from('>4I', DM[mid][0], 0x28)[2]
    print('=== mat %d lib Xbox %d: %d DRM %s' % (mid, dl, len(items), [(r, hashlib.md5(s.data).hexdigest()[:6]) for r, s in items]))
    s = items[0][1]
    if len({x.data for _, x in items}) > 1:
        a, b = items[0][1].data, items[1][1].data
        print('   copie diverse: byte diversi agli offset', [(i, a[i], b[i]) for i in range(len(a)) if a[i] != b[i]][:8])
    pc = struct.unpack_from('<4I', s.data, 0x28)[2]
    need = {k for k, x in enumerate(P[pc]['slots']) if x != 0xffffffff} if pc in P else set(range(8))
    print('   surrogato PC pos2 = %s (in P: %s), varianti da coprire %s' % (pc, pc in P, sorted(need)))
    cands = find_donors('D', dl, 0, want=12, prefer=[(x, pc) for x in rev[pc]])
    for c in cands[:12]:
        have = {k for k, x in enumerate(P[c[1]]['slots']) if x != 0xffffffff}
        r1 = find_donors('D', dl, 1, want=1, prefer=[c])
        print('   candidato donatore %s: varianti %s, copre need: %s, slot1 ok: %s' % (c, sorted(have), need <= have, bool(r1 and r1[0] == c)))
    ok_any = False
    for c in cands:
        have = {k for k, x in enumerate(P[c[1]]['slots']) if x != 0xffffffff}
        if not need <= have: continue
        r1 = find_donors('D', dl, 1, want=1, prefer=[c])
        if not (r1 and r1[0] == c): continue
        xs, pd = c; bridge = material_pairs(xs, pd)
        try:
            mres, ties = mp_resolve.resolve(xs, pd); mres, ties, sn = struct_resolve.apply(xs, pd, mres, ties)
        except Exception as ex: print('   donatore %s: regola famiglia ECCEZIONE %s' % (c, repr(ex)[:100])); continue
        XPm = params(f9_common._Sec(*DM[mid]), 'be'); PPm = params(s, 'le')
        try: slotmap, rows = F14.derive_slotmap(mid, dl, s.data, s.reloc)
        except Exception as ex: print('   slotmap:', repr(ex)[:150]); break
        mo = material_opts(mid); mo2 = dict(mo)
        if 'alpha1' in mo: mo2['alpha1'] = {slotmap[x] for x in mo['alpha1']}
        res_k = []; bad = None
        for k, e in enumerate(P[pd]['slots']):
            if e == 0xffffffff: continue
            preg = {n: ri for n, rs, ri, rc in f9m.pc_ctab(P[pd]['entries'][e]['blob']) if rs == 3}
            xblob = D[dl]['entries'][D[dl]['slots'][k & 1]]['blob']
            try:
                T, info = f9m.build(xblob, P[pd]['entries'][e]['blob'], X[xs]['entries'][X[xs]['slots'][k & 1]]['blob'], [(m_[2], m_[3]) for m_ in bridge], log=[], x_opts=mo2, x_samp_names=F14.SlotMapSpec(slotmap, preg), mp_res=mres)
                for lane, cs in info['ties'].items(): raise f9m.Fail('pareggio %s' % (lane,))
                T, _ = T3.apply_virt(T, info['virt'], XPm); T, _ = bind_material(T, XPm, PPm); T, nleg = T3.legalize_consts(T)
                bc = sm3asm.encode(T); n, probs = F14.offline_checks(T, bc)
                if probs: raise f9m.Fail('controlli %s' % probs)
                res_k.append(n)
            except Exception as ex: bad = 'slot %d: %s %s' % (k, type(ex).__name__, str(ex)[:140]); break
        print('   donatore %s: lane PC %d, none %s -> %s' % (c, len(mres), [k for k, v in mres.items() if v[0] == 'none'], bad or 'COSTRUITO %d varianti (istr %s)' % (len(res_k), res_k)), flush=True)
        if not bad: ok_any = True; break
    if not ok_any: print('   -> nessun donatore costruisce tutte le varianti' if cands else '   -> nessun candidato')
