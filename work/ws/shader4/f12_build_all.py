"""F12 - trapianto luci su TUTTI i materiali DLC che usano una lib PS illuminata surrogata (generalizza f10).

Fase 1 (build):  python f12_build_all.py build
  - parte da work/baseline/B73/mods (nessun trapianto); per ogni DRM dell'overlay e ogni materiale (sezione tipo 10) il cui gemello Xbox
    ha in pos2 una lib illuminata (illuminati.tsv): cerca un donatore (blocco luci Xbox equivalente verificato su entrambi gli slot Xbox
    E varianti PC che coprono quelle del surrogato attuale), costruisce gli slot (f9.build + bind_material sui parametri del materiale),
    controlli offline (luci spente == traduzione Xbox, lint, istruzioni, letture non inizializzate, dcl/def, sampler <= s15);
  - esporta i bytecode in valid_all/<lib>_s<k>.bin e salva il piano in f12_plan.pkl / f12_report.md.
Fase 2 (VM, a mano o da Claude):
  C:\\Windows\\SysWOW64\\WindowsPowerShell\\v1.0\\powershell.exe -NoProfile -ExecutionPolicy Bypass -File Z:\\tru-port\\tools\\vm_ps_draw.ps1
      -Dir Z:\\tru-port\\work\\ws\\shader4\\valid_all -Dll "<gioco>\\d3d9.dll"     (cwd = cartella del gioco)
Fase 3 (assemble): python f12_build_all.py assemble
  - legge valid_all/draw_result.txt: include SOLO le lib con tutti gli slot OK; scrive i DRM in B78/ e il riassunto.
"""
import sys, os, json, hashlib, struct, collections, csv, pickle, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from f10_build_dlc import *
from f11_uninit import uninit_reads, decl_problems

SRC = os.path.join(ROOT, 'work/baseline/B73/mods')
VAL = os.path.join(HERE, 'valid_all')
OUTD = os.path.join(HERE, 'B83')
PLAN = os.path.join(HERE, 'f12_plan.pkl')


def offline_ok(T, xblob, XPm, opts=None):
    n = len(body(T))
    off = lights_off_check(T, xblob, XPm, opts=opts)
    bc = sm3asm.encode(T)
    errs = f4_lint.lint(bc, True)
    un = uninit_reads(T); dp = decl_problems(T)
    smax = max([i.ops[0].num for i in header(T) if i.op == 'dcl' and i.ops[0].rtype == sm3asm.RT_SAMPLER] + [0])
    probs = []
    if n > 1024: probs.append('istr %d' % n)   # dgVoodoo accetta e disegna fino a 2000 (verificato in VM 14/10)
    if off < 0.99: probs.append('luci spente %.3f' % off)
    if errs: probs.append('lint %s' % errs[:2])
    if un: probs.append('non inizializzati %d' % len(un))
    if dp: probs.append('dcl %s' % dp[:2])
    if smax > 15: probs.append('sampler s%d' % smax)
    return bc, n, off, probs


_TEXF = None
REENCODED = {6610}


def tex_formats():
    """{id texture: (formato Xbox gpu, fourcc/formato PC)} da tutti i DRM DLC Xbox grezzi e dai DRM PC di B73."""
    global _TEXF
    if _TEXF is not None: return _TEXF
    import convert_dlc
    xf, pf = {}, {}
    for path in glob.glob(os.path.join(SRC, '**', '*.drm'), recursive=True):
        try:
            d = drm_write.read(open(path, 'rb').read(), 'le')
            for s_ in d.sections:
                if s_.type == 5: pf.setdefault(s_.id, struct.unpack_from('<I', s_.data, 4)[0])
            raw, _ = convert_dlc.raw_dlc(os.path.basename(path)); xd = drm_write.read(raw, 'be')
            for s_ in xd.sections:
                if s_.type == 5: xf.setdefault(s_.id, struct.unpack_from('>I', s_.data, 4)[0] & 0x3f)
        except Exception:
            continue
    _TEXF = (xf, pf); return _TEXF


def material_opts(mid):
    """opzioni del traduttore per il materiale: alpha1 = slot con texture DXT1 su Xbox e DXT5 sul PC."""
    import drm_reloc as R_
    xf, pf = tex_formats(); L = libs(); d, r = L['DM'][mid]
    T = dict(R_.parse(r, 'be').internal)[0x54]; nt = d[0x52]; a1 = set()
    for k in range(nt):
        tid, _a, _t, _f, slot, _fl = struct.unpack_from('>IIIBBH', d, T + 16 * k)
        # solo texture DLC ricodificate da noi (web_cutout: 6610 DXT1 alfa 255 -> DXT5 alfa = 2*luminanza); le texture del gioco base
        # convertite dal porting ufficiale (id < 5000) restano come sono
        if tid in REENCODED and xf.get(tid) == 0x12 and pf.get(tid) == 0x35545844: a1.add(slot)
    return {'alpha1': a1} if a1 else {}


def material_occurrences(src, DM, accept):
    """({mid: [(rel, sezione materiale)]}, {rel: {(tipo, id): sezione}}) sui DRM sotto src; accept(lib Xbox del materiale)."""
    occ = collections.defaultdict(list); secs = {}
    for path in sorted(glob.glob(os.path.join(src, '**', '*.drm'), recursive=True)):
        rel = os.path.relpath(path, src)
        try: d = drm_write.read(open(path, 'rb').read(), 'le')
        except Exception: continue
        secs[rel] = {(s.type, s.id): s for s in d.sections}
        for (t, mid), s in sorted(secs[rel].items()):
            if t == 10 and mid in DM and accept(struct.unpack_from('>4I', DM[mid][0], 0x28)[2]): occ[mid].append((rel, s))
    return occ, secs


_DLCMAP = None


def original_surrogate(dl):
    global _DLCMAP
    if _DLCMAP is None: _DLCMAP = json.load(open(os.path.join(ROOT, 'work/render/dlc_shader_map.json')))
    return _DLCMAP[str(dl)]['pc']


def canonical_material(items):
    """Sezione materiale unica per tutti i DRM, o None. Copie diverse si unificano solo se stessa lunghezza e stessi reloc e UNA sola e'
    nel DRM di livello (non in streamgroups/): le copie degli streamgroup sono rimaste indietro rispetto ai fix del livello (es. 23396:
    moltiplicatori B41 8x/15x ancora presenti nella copia water_wheel, gia' riportati a 1.0 nel livello da B42)."""
    if len({s.data for _, s in items}) == 1: return items[0][1]
    if len({(len(s.data), s.reloc) for _, s in items}) != 1: return None
    lvl = [s for rel, s in items if not rel.startswith('streamgroups' + os.sep) and not rel.startswith('streamgroups/')]
    return lvl[0] if len(lvl) == 1 else None


def shared_problem(dl, items, secs):
    """Perche' un materiale non si puo' trapiantare, o None. Le sezioni sono condivise PER ID fra i DRM residenti: la lib nuova deve
    entrare in TUTTI i DRM che hanno il materiale, con materiale e lib identici, altrimenti scaricando un DRM il materiale tenuto vivo
    da un altro punta a una lib liberata (crash B82). Solo materiali ancora sul surrogato originale: gli altri hanno un fix nostro."""
    s = canonical_material(items)
    if s is None: return 'sezione materiale diversa fra DRM, nessuna copia canonica'
    pcs = {struct.unpack_from('<I', x.data, 0x30)[0] for _, x in items}
    pc = struct.unpack_from('<4I', s.data, 0x28)[2]
    if len(pcs) > 1 or original_surrogate(dl) != pc: return 'pos2 PC %s diverso dal surrogato originale (fix altrui)' % sorted(pcs)
    miss = [rel for rel, _ in items if (9, pc) not in secs[rel]]
    if miss: return 'surrogato PC %d assente in %s' % (pc, miss[0])
    return None


def build_phase():
    L = libs(); D, DM, X, P = L['D'], L['DM'], L['X'], L['P']
    lit = {int(r['id_xbox']): r for r in csv.DictReader(open(os.path.join(HERE, 'illuminati.tsv')), delimiter='\t')}
    rev = collections.defaultdict(list)
    for x, p in x2p().items(): rev[p].append(x)
    hs_all, ids_used = all_hashes(); taken = set(hs_all)
    free_ids = [i for i in range(2721, 6000) if i not in ids_used and i not in D and i not in P and i not in X]
    os.makedirs(VAL, exist_ok=True)
    for f in glob.glob(os.path.join(VAL, '*.bin')): os.remove(f)
    donor_cache = {}; plan = []; log = []; cnt = collections.Counter()
    occ, secs = material_occurrences(SRC, DM, lambda dl: dl in lit)
    for mid, items in sorted(occ.items()):
        dl = struct.unpack_from('>4I', DM[mid][0], 0x28)[2]
        why = shared_problem(dl, items, secs)
        if why:
            log.append('mat %d lib %d (%d DRM): %s' % (mid, dl, len(items), why)); cnt['non trapiantabile come unita'] += 1; continue
        s = canonical_material(items); pc = struct.unpack_from('<4I', s.data, 0x28)[2]
        if dl not in donor_cache:
            need = {k for k, x in enumerate(P[pc]['slots']) if x != 0xffffffff} if pc in P else set(range(8))
            pref = [(x, pc) for x in rev[pc]]
            ok = None
            for cand in find_donors('D', dl, 0, want=12, prefer=pref):
                have = {k for k, x in enumerate(P[cand[1]]['slots']) if x != 0xffffffff}
                if not need <= have: continue
                r1 = find_donors('D', dl, 1, want=1, prefer=[cand])
                if r1 and r1[0] == cand: ok = cand; break
            donor_cache[dl] = ok
            print('lib %d: donatore %s' % (dl, ok), flush=True)
        dn = donor_cache[dl]
        if dn is None:
            log.append('mat %d lib %d: nessun donatore equivalente con varianti complete' % (mid, dl)); cnt['nessun donatore'] += 1; continue
        xs, pd = dn
        bridge = material_pairs(xs, pd)
        XPm = params(f9_common._Sec(*DM[mid]), 'be'); PPm = params(s, 'le')
        slots = []; bad = None
        for k, e in enumerate(P[pd]['slots']):
            if e == 0xffffffff: slots.append(None); continue
            xblob = D[dl]['entries'][D[dl]['slots'][k & 1]]['blob']
            try:
                mo = material_opts(mid)
                T, info = build(xblob, P[pd]['entries'][e]['blob'], X[xs]['entries'][X[xs]['slots'][k & 1]]['blob'], [(m_[2], m_[3]) for m_ in bridge], log=[], x_opts=mo)
                T, binfo = bind_material(T, XPm, PPm)
                bc, n, off, probs = offline_ok(T, xblob, XPm, opts=mo)
            except (Fail, xenos2sm3.Reject) as ex:
                bad = 'slot %d: %s' % (k, str(ex)[:120]); break
            if probs: bad = 'slot %d: %s' % (k, probs); break
            slots.append(bc)
        if bad:
            log.append('mat %d lib %d: %s' % (mid, dl, bad)); cnt['controllo offline fallito'] += 1; continue
        lid = free_ids.pop(0)   # UNA lib per materiale, uguale in tutti i DRM che lo contengono
        for k, bc in enumerate(slots):
            if bc is not None: open(os.path.join(VAL, 'lib%d_s%d.bin' % (lid, k)), 'wb').write(bc)
        for rel, _ in items: plan.append(dict(drm=rel, mat=mid, dlc=dl, old=pc, lib=lid, donor=dn, slots=slots, canon=s.data))
        cnt['costruita'] += 1
        print('  mat %d lib %d -> %d (donatore %s) in %d DRM' % (mid, dl, lid, dn, len(items)), flush=True)
    pickle.dump(dict(plan=plan, log=log), open(PLAN, 'wb'))
    md = ['# F12 trapianto su tutti i materiali illuminati (fase build)', '', ', '.join('%s %d' % kv for kv in cnt.most_common()), '',
          'Lib DLC con donatore: %d / %d' % (sum(1 for v in donor_cache.values() if v), len(donor_cache)),
          'Materiali costruiti: %d (bytecode in valid_all/, %d file)' % (len({it['mat'] for it in plan}), len(glob.glob(os.path.join(VAL, '*.bin')))), '', '## Esclusi'] + ['- ' + l for l in log]
    open(os.path.join(HERE, 'f12_report.md'), 'w').write('\n'.join(md) + '\n')
    print('\n'.join(md[:6]))


def assemble_phase():
    data = pickle.load(open(PLAN, 'rb')); plan = data['plan']
    res = {}
    for line in open(os.path.join(VAL, 'draw_result.txt'), encoding='ascii', errors='replace'):
        if '`t' in line or '\t' in line:
            name, r = line.replace('`t', '\t').split('\t', 1)
            res[name.strip()] = all(v.endswith('0x00000000') for v in r.split())
    ok_plan = []; rej = []
    for it in plan:
        names = ['lib%d_s%d.bin' % (it['lib'], k) for k, bc in enumerate(it['slots']) if bc is not None]
        if all(res.get(n) for n in names): ok_plan.append(it)
        else: rej.append('%s mat %d lib %d: VM %s' % (it['drm'], it['mat'], it['lib'], [n for n in names if not res.get(n)]))
    hs_all, _ = all_hashes(); taken = set(hs_all)
    os.makedirs(OUTD, exist_ok=True)
    by_drm = collections.defaultdict(list)
    for it in ok_plan: by_drm[it['drm']].append(it)
    out = {}; libbytes = {}
    for rel, items in sorted(by_drm.items()):
        raw = open(os.path.join(SRC, rel), 'rb').read(); d = drm_write.read(raw, 'le'); secs = list(d.sections)
        for it in items:
            if it['lib'] not in libbytes: libbytes[it['lib']] = build_lib(it['slots'], taken)[0]   # stessi byte in ogni DRM
            sec_bytes = libbytes[it['lib']]
            tmpl = next(s for s in secs if s.type == 9 and s.id == it['old'])
            secs.insert(secs.index(tmpl) + 1, drm_write.Section(9, it['lib'], sec_bytes, b'', flags=tmpl.flags, ver=tmpl.ver, spec=tmpl.spec, pad=tmpl.pad))
            m = next(s for s in secs if s.type == 10 and s.id == it['mat'])
            assert struct.unpack_from('<I', m.data, 0x30)[0] == it['old'] and len(m.data) == len(it['canon'])
            data_ = bytearray(it['canon']); struct.pack_into('<I', data_, 0x30, it['lib']); m.data = bytes(data_)   # materiale unificato
        d.sections = secs; out_raw = d.write('le')
        a = {(s.type, s.id): s for s in drm_write.read(raw, 'le').sections}; b = {(s.type, s.id): s for s in drm_write.read(out_raw, 'le').sections}
        assert set(b) - set(a) == {(9, it['lib']) for it in items} and set(a) <= set(b), rel
        mats = {it['mat']: it for it in items}
        for key, s in a.items():
            t = b[key]
            assert (t.reloc, t.flags, t.ver, t.spec, t.pad) == (s.reloc, s.flags, s.ver, s.spec, s.pad), (rel, key)
            if t.data != s.data:
                assert key[0] == 10 and key[1] in mats, (rel, key)
                want = bytearray(mats[key[1]]['canon']); struct.pack_into('<I', want, 0x30, mats[key[1]]['lib'])
                assert t.data == bytes(want), (rel, key)
        first9 = min(i for i, s in enumerate(drm_write.read(raw, 'le').sections) if s.type == 9)
        mx = max((si for s in drm_write.read(raw, 'le').sections for si, _, _ in R.parse(s.reloc, 'le').external), default=-1)
        assert mx < first9, (rel, mx, first9)
        enc = drm_write.cdrm_encode(out_raw, 'le')
        os.makedirs(os.path.dirname(os.path.join(OUTD, rel)), exist_ok=True)
        open(os.path.join(OUTD, rel), 'wb').write(enc); out[rel] = (len(items), hashlib.md5(enc).hexdigest())
        print('scritto', rel, 'materiali', len(items))
    md = ['# F12 fase assemble', '', 'Materiali inclusi: %d, scartati dalla VM: %d, DRM scritti: %d' % (len(ok_plan), len(rej), len(out)), ''] + \
         ['- %s: %d materiali, md5 %s' % (r, n, h) for r, (n, h) in out.items()] + ['', '## Scartati dalla VM'] + ['- ' + l for l in rej]
    open(os.path.join(HERE, 'f12_assemble.md'), 'w').write('\n'.join(md) + '\n'); print('\n'.join(md[:3]))


if __name__ == '__main__':
    {'build': build_phase, 'assemble': assemble_phase}[sys.argv[1] if len(sys.argv) > 1 else 'build']()
