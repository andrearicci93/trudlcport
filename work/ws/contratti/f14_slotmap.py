"""F14 - contratto sampler dei PS trapiantati (f12): i sampler del materiale vanno numerati come gli slot PC del materiale.

DIFETTO (verificato sui dati, 16/10/2026). f12 traduce la superficie Xbox con xsamp(): per i sampler 'p_default*' il registro PC e'
l'INDICE DI FETCH Xbox (= slot Xbox). Ma 21 dei 35 materiali trapiantati erano stati rimappati da material_reslot (B73) sugli slot del
surrogato PC (la lib PS originale). Il materiale e' rimasto cosi' (passi 0, 1, 3 sono lib PC adattate a quegli slot), la lib nuova no:
il PS campiona s_c con la numerazione Xbox, il motore lega l'entry k allo slot PC. Il gate di f12 (lights_off_check) non poteva vederlo:
sm3vm.det_tex(lambda s: s) rende la texture funzione del REGISTRO, quindi traduzione e riferimento concordano per costruzione.

CORREZIONE. Lato shader, il materiale non si tocca: mappa  registro Xbox c  ->  slot PC dell'entry che l'Xbox legava a c
(stesso ordine di entry, stessi tipi/flag: verificato). La mappa e' emessa dalla stessa trasformazione che genera il bytecode
(xsamp con SlotMapSpec) e salvata nel manifest laterale contracts.json. Anche l'opzione alpha1 (per registro PC) viene rimappata.
Gate nuovo: entry_equivalence(): le texture del ramo Xbox dipendono dall'entry legata dallo slot Xbox, quelle del ramo PC
dall'entry legata dallo slot PC. Sui 21 deve fallire PRIMA e passare DOPO; sui 14 con slot identici passare in entrambi i casi.

Uso (cwd = radice del progetto):
  tools/venv/bin/python -I work/ws/contratti/f14_slotmap.py check  [BASELINE=B84]      prima: gate contratto sulle lib attuali
  tools/venv/bin/python -I work/ws/contratti/f14_slotmap.py identity [N]               rebuild con mappa identita' == B84 byte per byte
  tools/venv/bin/python -I work/ws/contratti/f14_slotmap.py build  [BASELINE=B84]      ricostruisce, verifica, scrive out/
  tools/venv/bin/python -I work/ws/contratti/f14_slotmap.py verify MODS_DIR [BASELINE=B84]   gate sui byte REALI di un albero (dopo)
Nessuna scrittura fuori da work/ws/contratti/out/. Non tocca l'installazione ne' le baseline.
"""
import sys, os, struct, pickle, collections, hashlib, json, glob, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
S4 = os.path.join(ROOT, 'work/ws/shader4')
sys.path.insert(0, S4); sys.path.insert(0, HERE)
import f9_transplant as F9
import f10_build_dlc as F10
import f12_build_all as F12
import f4_build, f4_lint
from f3_common import libs, sm3asm, sm3dis, sm3vm, shaderlib, xenos2sm3
import xenos_xlat as XL
import drm_write, drm_reloc as R
import contract as C

PLAN = os.path.join(S4, 'f12_plan.pkl')
OUT = os.path.join(HERE, 'out')
TH = 0.99          # soglia dell'equivalenza (come lights_off_check)
SEED = 11


# ------------------------------------------------------------------------------------------------ mappa dei sampler
class SlotMapSpec:
    """Sostituisce x_samp_names in f9_transplant.build: registro Xbox -> slot PC per i sampler p_default*; nomi globali -> donatore."""
    def __init__(self, slotmap, preg):
        self.slotmap, self.preg = dict(slotmap), dict(preg)


_orig_xsamp = F9.xsamp


def _xsamp(xblob, regs_by_name):
    if isinstance(regs_by_name, SlotMapSpec):
        sm = {c['reg']: c['name'] for c in XL.parse(xblob).ctab if c['set'] == 3}
        def f(name, c):
            n = sm.get(c, name)
            if n.startswith('p_default'): return regs_by_name.slotmap.get(c, c)
            return regs_by_name.preg.get(n, c)
        return f
    return _orig_xsamp(xblob, regs_by_name)


F9.xsamp = _xsamp


def xbox_sampler_names(dl):
    """{registro fetch Xbox: nome} (set 3 della CTAB, unione delle due varianti Xbox della lib DLC dl)."""
    D = libs()['D']; lib = D[dl]; names = {}
    for s in set(lib['slots']) - {0xFFFFFFFF}:
        for c in XL.parse(lib['entries'][s]['blob']).ctab:
            if c['set'] == 3: names.setdefault(c['reg'], c['name'])
    return names


def derive_slotmap(mid, dl, pc_data, pc_reloc):
    """Mappa dalla trasformazione: entry k dell'Xbox (slot Xbox, nome del sampler) <-> entry k del materiale PC (slot PC).
    Precondizioni verificate: stesso numero di entry, stesso tipo e stesso flag nello stesso ordine, slot unici da entrambe le parti."""
    xd, xr = libs()['DM'][mid]
    xe = C.entries(xd, xr, 'be'); pe = C.entries(pc_data, pc_reloc, 'le')
    if len(xe) != len(pe): raise ValueError('mat %d: %d entry Xbox, %d PC' % (mid, len(xe), len(pe)))
    names = xbox_sampler_names(dl)
    rows = []
    for k, (a, b) in enumerate(zip(xe, pe)):
        if a['type'] != b['type'] or a['flag'] != b['flag']:
            raise ValueError('mat %d entry %d: tipo/flag Xbox %s/%s PC %s/%s' % (mid, k, a['type'], a['flag'], b['type'], b['flag']))
        rows.append(dict(entry=k, sampler=names.get(a['slot']), xbox_reg=a['slot'], pc_slot=b['slot'], type=a['type'], flag=a['flag'],
                         xbox_tex=a['tex'], pc_tex=b['tex']))
    if len({r['xbox_reg'] for r in rows}) != len(rows) or len({r['pc_slot'] for r in rows}) != len(rows):
        raise ValueError('mat %d: slot non unici' % mid)
    slotmap = {r['xbox_reg']: r['pc_slot'] for r in rows}
    return slotmap, rows


# ------------------------------------------------------------------------------------------------ gate: equivalenza con texture per entry
def entry_equivalence(prog_pc, xblob, XPm, xopts, xslot2entry, pslot2entry, seed=SEED):
    """Frazione di campioni in cui il PS PC (luci spente, bool tutti falsi) == traduzione Xbox con luci spente, quando la texture letta
    da un sampler e' una funzione deterministica dell'ENTRY legata a quello slot (Xbox: slot Xbox; PC: slot PC)."""
    pct = []; K = F9.Consts(pct)
    sh = XL.parse(xblob); bn = F9.bool_names(sh)
    bools = {i: 0 for i in bn}
    o = dict(xopts or {}); o['noopt'] = True
    t = xenos2sm3.translate(xblob, K.fn, bools=bools, samp=lambda n, c: c, opts=o)
    progX = sm3asm.parse_text(t.text)
    envX = F9.Env(seed, XPm); envP = F9.Env(seed, XPm)
    envX.tex = sm3vm.det_tex(lambda s: ('entry', xslot2entry[s]) if s in xslot2entry else ('reg', s))
    envP.tex = sm3vm.det_tex(lambda s: ('entry', pslot2entry[s]) if s in pslot2entry else ('reg', s))
    a = envP.run(prog_pc, F9.body(prog_pc), envP.state0(prog_pc), {})
    b = envX.run(progX, F9.body(progX), envX.state0(progX), {})
    ca, cb = a[0].get((sm3asm.RT_COLOROUT, 0)), b[0].get((sm3asm.RT_COLOROUT, 0))
    if ca is None or cb is None: return 0.0
    import numpy as np
    return float((np.isclose(ca, cb, **F9.TOL).all(axis=1) & (a[1] == b[1]) | (a[1] & b[1])).mean())


def contract_gate(bc_by_slot, dl, rows, xopts, XPm):
    """Per ogni variante PC k: equivalenza ramo Xbox (variante k&1) vs ramo PC. -> {k: frazione}."""
    D = libs()['D']
    xs2e = {r['xbox_reg']: r['entry'] for r in rows}; ps2e = {r['pc_slot']: r['entry'] for r in rows}
    res = {}
    for k, bc in bc_by_slot.items():
        xblob = D[dl]['entries'][D[dl]['slots'][k & 1]]['blob']
        res[k] = entry_equivalence(sm3asm.decode(bc), xblob, XPm, xopts, xs2e, ps2e)
    return res


# ------------------------------------------------------------------------------------------------ permutazione a posteriori (riprova indipendente)
def permute_samplers(bc, perm):
    """Rinumera i registri sampler del bytecode (dcl e operandi texld) con perm {vecchio: nuovo}."""
    p = sm3asm.decode(bc)
    for i in p.instrs():
        for o in i.ops:
            if o.rtype == sm3asm.RT_SAMPLER: o.num = perm.get(o.num, o.num)
    return sm3asm.encode(p)


def canon_text(bc):
    """Testo del programma con le dcl di sampler ordinate (l'ordine delle dcl non ha effetto)."""
    lines = sm3asm.format_program(sm3asm.decode(bc)).splitlines()
    head = [l for l in lines[1:] if l.startswith('dcl_') or l.startswith('def ')]
    body = [l for l in lines[1:] if not (l.startswith('dcl_') or l.startswith('def '))]
    return lines[0], sorted(head), body


# ------------------------------------------------------------------------------------------------ rebuild
def plan_by_material():
    plan = pickle.load(open(PLAN, 'rb'))['plan']
    out = collections.OrderedDict()
    for it in plan:
        m = out.setdefault(it['mat'], dict(mat=it['mat'], lib=it['lib'], dlc=it['dlc'], old=it['old'], donor=it['donor'], canon=it['canon'],
                                           slots=it['slots'], drms=[]))
        assert m['lib'] == it['lib'] and m['donor'] == it['donor'] and m['slots'] == it['slots'], it['mat']
        m['drms'].append(it['drm'])
    return out


def load_parent(base):
    """Albero del genitore: {rel: Drm}. Precondizione: le lib e i materiali del piano coincidono con quelli dell'albero."""
    mods = os.path.join(ROOT, 'work/baseline', base, 'mods')
    return mods, C.read_tree(mods)


def check_parent(plan, tree):
    """Ogni lib (9, id) e ogni materiale (10, id) del piano, in ogni DRM, ha i byte di f12 (materiale: canon + pos2 = lib)."""
    errs = []
    for mid, m in plan.items():
        for rel in m['drms']:
            d = tree[rel]; secs = {(s.type, s.id): s for s in d.sections}
            ms = secs.get((10, mid)); ls = secs.get((9, m['lib']))
            if ms is None or ls is None: errs.append('%s mat %d: sezione assente' % (rel, mid)); continue
            want = bytearray(m['canon']); struct.pack_into('<I', want, 0x30, m['lib'])
            if ms.data != bytes(want): errs.append('%s mat %d: materiale diverso dal piano f12' % (rel, mid))
            f = C.frame_lib(ls.data)
            if f['errors']: errs.append('%s lib %d: framing %s' % (rel, m['lib'], f['errors'][:2]))
            for k, off in enumerate(f['slots']):
                if off == 0xFFFFFFFF:
                    if m['slots'][k] is not None: errs.append('%s lib %d slot %d assente' % (rel, m['lib'], k))
                elif m['slots'][k] != f['entries'][off]['bc']: errs.append('%s lib %d slot %d: bytecode diverso dal piano f12' % (rel, m['lib'], k))
    return errs


def rebuild_material(m, slotmap, rows, log=None):
    """Ricostruisce tutte le varianti della lib di un materiale con la mappa dei sampler. -> (dict k -> bytecode, info per variante)."""
    L = libs(); D, DM, X, P = L['D'], L['DM'], L['X'], L['P']
    mid, dl = m['mat'], m['dlc']; xs, pd = m['donor']
    secPC = m['_pcsec']                           # sezione materiale PC canonica del genitore (data + reloc) per params()
    bridge = F9.material_pairs(xs, pd)
    XPm = F10.params(F10.f9_common._Sec(*DM[mid]), 'be'); PPm = F10.params(secPC, 'le')
    mo = F12.material_opts(mid)
    mo2 = dict(mo)
    if 'alpha1' in mo: mo2['alpha1'] = {slotmap[s] for s in mo['alpha1']}
    engine_regs = set()
    out, info = {}, {}
    for k, e in enumerate(P[pd]['slots']):
        if e == 0xFFFFFFFF: continue
        preg = {n: ri for n, rs, ri, rc in F9.pc_ctab(P[pd]['entries'][e]['blob']) if rs == 3}   # come in f9_transplant.build
        engine_regs |= {r for n, r in preg.items() if not n.startswith('p_default')}
        spec = SlotMapSpec(slotmap, preg)
        xblob = D[dl]['entries'][D[dl]['slots'][k & 1]]['blob']
        T, binfo = F9.build(xblob, P[pd]['entries'][e]['blob'], X[xs]['entries'][X[xs]['slots'][k & 1]]['blob'],
                            [(m_[2], m_[3]) for m_ in bridge], log=[], x_opts=mo2, x_samp_names=spec)
        T, bi = F10.bind_material(T, XPm, PPm)
        out[k] = (T, mo2, XPm)
    return out, dict(alpha1_xbox=sorted(mo.get('alpha1', ())), alpha1_pc=sorted(mo2.get('alpha1', ())), engine_regs=sorted(engine_regs))


def offline_checks(T, bc):
    """Controlli di f12.offline_ok senza il confronto 'luci spente' (sostituito dal gate di contratto)."""
    n = len(F9.body(T))
    errs = f4_lint.lint(bc, True)
    un = F12.uninit_reads(T); dp = F12.decl_problems(T)
    smax = max([i.ops[0].num for i in F9.header(T) if i.op == 'dcl' and i.ops[0].rtype == sm3asm.RT_SAMPLER] + [0])
    probs = []
    if n > 1024: probs.append('istr %d' % n)
    if errs: probs.append('lint %s' % errs[:2])
    if un: probs.append('non inizializzati %d' % len(un))
    if dp: probs.append('dcl %s' % dp[:2])
    if smax > 15: probs.append('sampler s%d' % smax)
    return n, probs


# ------------------------------------------------------------------------------------------------ comandi
def prepare(base):
    plan = plan_by_material()
    mods, tree = load_parent(base)
    errs = check_parent(plan, tree)
    for mid, m in plan.items():                       # sezione materiale canonica (con reloc) dal genitore
        rel = m['drms'][0]; s = {(x.type, x.id): x for x in tree[rel].sections}[(10, mid)]
        m['_pcsec'] = s
    return plan, mods, tree, errs


def cmd_check(base):
    plan, mods, tree, errs = prepare(base)
    print('genitore', base, '| piano f12: %d materiali, %d occorrenze | incoerenze con l\'albero: %d' % (len(plan), sum(len(m['drms']) for m in plan.values()), len(errs)))
    for e in errs[:10]: print('  !!', e)
    res = collections.OrderedDict()
    for mid, m in plan.items():
        pe = m['_pcsec']
        slotmap, rows = derive_slotmap(mid, m['dlc'], pe.data, pe.reloc)
        ident = all(a == b for a, b in slotmap.items())
        mo = F12.material_opts(mid)
        XPm = F10.params(F10.f9_common._Sec(*libs()['DM'][mid]), 'be')
        bcs = {k: b for k, b in enumerate(m['slots']) if b is not None}
        g = contract_gate(bcs, m['dlc'], rows, mo, XPm)
        res[mid] = dict(identity=ident, gate=g, lib=m['lib'])
        print('mat %5d lib %d slot==Xbox %-5s | gate min %.3f  per variante %s' % (mid, m['lib'], ident, min(g.values()), {k: round(v, 3) for k, v in g.items()}), flush=True)
    bad = [mid for mid, r in res.items() if min(r['gate'].values()) < TH]
    ident_ok = [mid for mid, r in res.items() if r['identity'] and mid not in bad]
    print('\nPRIMA: gate fallito su %d/%d materiali: %s' % (len(bad), len(res), bad))
    print('       slot identici all\'Xbox e gate ok: %d' % len(ident_ok))
    print('       discordanze fra "slot != Xbox" e "gate fallito":', sorted(set(m for m, r in res.items() if (not r['identity']) != (m in bad))))
    return res


def cmd_verify(mods_dir, base):
    """Gate di contratto sui byte realmente presenti in un albero: ogni lib del piano, in OGNI DRM che la contiene, per ogni variante."""
    plan, _, tree_parent, errs = prepare(base)           # solo per materiale canonico/mappa (dal genitore) e piano
    tree = C.read_tree(mods_dir)
    bad = []; n_ok = 0
    for mid, m in plan.items():
        pe = m['_pcsec']
        slotmap, rows = derive_slotmap(mid, m['dlc'], pe.data, pe.reloc)
        mo = F12.material_opts(mid)
        XPm = F10.params(F10.f9_common._Sec(*libs()['DM'][mid]), 'be')
        copies = {}
        for rel in m['drms']:
            sec = {(s.type, s.id): s for s in tree[rel].sections}[(9, m['lib'])]
            ms = {(s.type, s.id): s for s in tree[rel].sections}[(10, mid)]
            want = bytearray(m['canon']); struct.pack_into('<I', want, 0x30, m['lib'])
            if ms.data != bytes(want): bad.append('%s mat %d: materiale cambiato rispetto al piano' % (rel, mid))
            copies[rel] = sec.data
        if len(set(copies.values())) != 1: bad.append('mat %d lib %d: copie diverse fra DRM %s' % (mid, m['lib'], sorted(copies)))
        f = C.frame_lib(next(iter(copies.values())))
        if f['errors']: bad.append('lib %d framing %s' % (m['lib'], f['errors'][:1]))
        bcs = {k: f['entries'][o]['bc'] for k, o in enumerate(f['slots']) if o != 0xFFFFFFFF}
        if set(bcs) != {k for k, b in enumerate(m['slots']) if b is not None}: bad.append('mat %d: varianti diverse' % mid)
        g = contract_gate(bcs, m['dlc'], rows, mo, XPm)
        if min(g.values()) < TH: bad.append('mat %d lib %d: gate %s' % (mid, m['lib'], {k: round(v, 3) for k, v in g.items()}))
        else: n_ok += 1
    print('verify %s: materiali %d, gate ok %d, problemi %d' % (mods_dir, len(plan), n_ok, len(bad)))
    for b in bad: print('  !!', b)
    return 1 if bad else 0


def cmd_identity(base, n):
    plan, mods, tree, errs = prepare(base)
    done = 0
    for mid, m in plan.items():
        pe = m['_pcsec']
        slotmap, rows = derive_slotmap(mid, m['dlc'], pe.data, pe.reloc)
        if not all(a == b for a, b in slotmap.items()): continue
        t0 = time.time()
        built, info = rebuild_material(m, slotmap, rows)
        same = True
        for k, (T, mo2, XPm) in built.items():
            bc = sm3asm.encode(T)
            if bc != m['slots'][k]:
                same = False; print('  mat %d slot %d: rebuild identita\' DIVERSO da B83 (%d vs %d byte)' % (mid, k, len(bc), len(m['slots'][k])))
        print('mat %d identita\': rebuild == B83 byte per byte: %s (%.1fs)' % (mid, same, time.time() - t0), flush=True)
        done += 1
        if done >= n: break


def build_all(base):
    plan, mods, tree, errs = prepare(base)
    if errs:
        print('PRECONDIZIONE FALLITA: %d incoerenze fra l\'albero %s e il piano f12:' % (len(errs), base))
        for e in errs[:20]: print('  ', e)
        sys.exit(2)
    taken, _ = f4_build.all_hashes()
    replaced_libs = set()
    manifest = collections.OrderedDict(); newlib = {}
    todo = []
    for mid, m in plan.items():
        pe = m['_pcsec']
        slotmap, rows = derive_slotmap(mid, m['dlc'], pe.data, pe.reloc)
        ident = all(a == b for a, b in slotmap.items())
        todo.append((mid, m, slotmap, rows, ident))
        if not ident: replaced_libs.add(m['lib'])
    # hash gia' occupati: quelli delle lib che restano (B84 meno le sostituite)
    for rel, d in tree.items():
        for s in d.sections:
            if s.type == 9 and s.id not in replaced_libs:
                for e in C.frame_lib(s.data)['entries'].values(): taken.add(e['hash'])
    for mid, m, slotmap, rows, ident in sorted(todo, key=lambda x: x[1]['lib']):
        entry = dict(material=mid, lib=m['lib'], dlc_lib=m['dlc'], donor=list(m['donor']), drms=m['drms'], identity=ident,
                     sampler_map=rows, old_variant_sha256={}, new_variant_sha256={})
        if ident:
            entry['action'] = 'invariata (slot PC == slot Xbox: contratto gia\' rispettato)'
            manifest[mid] = entry; continue
        t0 = time.time()
        built, info = rebuild_material(m, slotmap, rows)
        entry.update(info)
        bcs = {}; checks = {}
        mo = F12.material_opts(mid)
        XPm = F10.params(F10.f9_common._Sec(*libs()['DM'][mid]), 'be')
        for k, (T, mo2, _) in built.items():
            bc = sm3asm.encode(T)
            n, probs = offline_checks(T, bc)
            if probs: raise SystemExit('mat %d variante %d: %s' % (mid, k, probs))
            bcs[k] = bc
            # riprova indipendente: permutazione a posteriori del bytecode B83
            perm = {a: b for a, b in slotmap.items() if a != b}
            pp = permute_samplers(m['slots'][k], perm)
            cp = canon_text(pp) == canon_text(bc)
            # collisioni con i sampler del blocco luci
            used_new = set(slotmap.values())
            coll = sorted(used_new & set(info['engine_regs']))
            if coll: raise SystemExit('mat %d: slot PC %s collidono con i sampler del donatore' % (mid, coll))
            checks[k] = dict(istr=n, perm_posthoc_equal=cp)
            entry['old_variant_sha256'][k] = hashlib.sha256(m['slots'][k]).hexdigest()
            entry['new_variant_sha256'][k] = hashlib.sha256(bc).hexdigest()
        g = contract_gate(bcs, m['dlc'], rows, mo, XPm)
        for k in bcs: checks[k]['gate'] = g[k]
        entry['checks'] = checks
        if min(g.values()) < TH: raise SystemExit('mat %d: gate di contratto dopo la correzione %s' % (mid, g))
        sec_bytes, hs = f4_build.build_lib([bcs.get(k) for k in range(8)], taken)
        newlib[m['lib']] = sec_bytes
        entry['action'] = 'lib ricostruita con sampler rimappati'; entry['new_lib_hash8'] = hs
        manifest[mid] = entry
        print('mat %5d lib %d: ricostruita (%.1fs) gate dopo %s perm==rebuild %s' % (
            mid, m['lib'], time.time() - t0, {k: round(v, 3) for k, v in g.items()}, {k: v['perm_posthoc_equal'] for k, v in checks.items()}), flush=True)
    # assemblaggio: sostituisce SOLO i dati delle sezioni (9, lib) nei DRM del genitore
    os.makedirs(OUT, exist_ok=True)
    outdir = os.path.join(OUT, 'mods'); os.makedirs(outdir, exist_ok=True)
    changed = {}
    for rel, d in tree.items():
        libs_here = [s for s in d.sections if s.type == 9 and s.id in newlib]
        if not libs_here: continue
        raw = open(os.path.join(mods, rel), 'rb').read()
        d2 = drm_write.read(raw, 'le')
        for s in d2.sections:
            if s.type == 9 and s.id in newlib: s.data = newlib[s.id]
        out_raw = d2.write('le')
        a = {(s.type, s.id): s for s in drm_write.read(raw, 'le').sections}; b = {(s.type, s.id): s for s in drm_write.read(out_raw, 'le').sections}
        assert set(a) == set(b)
        for key, s in a.items():
            t = b[key]
            assert (t.reloc, t.flags, t.ver, t.spec, t.pad) == (s.reloc, s.flags, s.ver, s.spec, s.pad), (rel, key)
            if t.data != s.data: assert key[0] == 9 and key[1] in newlib, (rel, key)
        enc = drm_write.cdrm_encode(out_raw, 'le')
        p = os.path.join(outdir, rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'wb').write(enc)
        changed[rel] = dict(size=len(enc), md5=hashlib.md5(enc).hexdigest(), libs=sorted(s.id for s in libs_here))
        print('scritto', rel, changed[rel]['libs'])
    json.dump(dict(parent=base, parent_id=open(os.path.join(ROOT, 'work/baseline', base, 'id.txt')).read().strip(), changed=changed,
                   materials=manifest), open(os.path.join(OUT, 'contracts.json'), 'w'), indent=1, default=str)
    with open(os.path.join(OUT, 'md5.txt'), 'w') as f:
        for rel, c in sorted(changed.items()): f.write('%s  %s\n' % (c['md5'], rel))
    print('DRM scritti: %d; lib sostituite: %d (%s)' % (len(changed), len(newlib), sorted(newlib)))


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
    base = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].isdigit() else 'B84'
    if cmd == 'check': cmd_check(base)
    elif cmd == 'identity': cmd_identity(base, int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 3)
    elif cmd == 'build': build_all(base)
    elif cmd == 'verify': sys.exit(cmd_verify(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else 'B84'))
    else: sys.exit(__doc__)
