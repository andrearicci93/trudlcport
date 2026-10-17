"""F5 - censimento degli shader ILLUMINATI (54 lib DLC in illuminati.tsv): decide SE e DOVE conviene investire. Offline, deterministico.
Non costruisce niente e non tocca baseline/VM.

Misura:
 (a) DLC: per ogni lib x slot PS x permutazione dei bool (per nome, tutti gli elementi insieme) -> traduzione Xenos->SM3 con costanti
     finte associate per NOME (accetta anche p_Lights & co.) -> OK o motivo di rifiuto. Istogramma dei motivi = estensioni del traduttore
     che servirebbero (CUBE, predicati, loop...).
 (b) Stesso istogramma sulle coppie BASE illuminate Xbox<->PC (pos2): e' il tetto dell'oracolo offline per qualsiasi trapianto.
 (c) DLC vs gemello Xbox del surrogato PC (x2p inverso): firma CTAB normalizzata (shaderlib.norm_name) per nomi / count / registri,
     letterali def, e diff del testo Xenos (temp normalizzati) classificato per riga in:
        def   = cambiano solo letterali (costanti def)
        MP    = cambiano solo indice/swizzle di MaterialParams
        luci  = la riga tocca costanti luci
        strut = altro (struttura)
     Classe della lib = gruppo peggiore. def/MP sono correggibili con patch sul gemello PC SENZA tradurre le luci.
 (d) Materiali con difetti visibili (verde fluo / scarabocchi): quali lib illuminate usano e in che classe cadono.

Uso:  cd ~/Downloads/tru-port && tools/venv/bin/python -I work/ws/shader4/f5_census_lit.py
Uscita: work/ws/shader4/f5_census_lit.tsv (dettaglio), f5_census_lit.md (riassunto breve, da incollare a Claude)."""
import sys, os, csv, re, itertools, difflib, collections, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from f3_validate import *          # libs, x2p, positions, LIGHT, xenos2sm3, sm3asm, ...
import xenos_xlat as XL
from shaderlib import norm_name

# materiali con difetti visti dall'utente (verde fluo / scarabocchi rossi; RIPARTENZA.md, B41/B42)
DIFETTI = {20949: 'caverns_hall verde fluo', 21265: 'caverns_hall verde fluo', 23396: 'caverns_hall verde fluo+rosso',
           23397: 'caverns_hall verde fluo+rosso', 20883: 'caverns verde fluo', 23200: 'caverns verde fluo'}
LIGHTRX = re.compile(r'p_Lights|LightEnabled|p_ShadowEnabled|ParallelShadow|Irradiance|GlobalAmbientColor|ShadowMap|Attenuation')
OUT_TSV = os.path.join(HERE, 'f5_census_lit.tsv'); OUT_MD = os.path.join(HERE, 'f5_census_lit.md')


def reason(e):
    return re.sub(r'\d+', 'N', str(e))[:60]


def bool_names(sh):
    """{indice bool Xenos (sia reg che 128+reg) -> nome} dalla CTAB (set 0)."""
    out = {}
    for c in sh.ctab:
        if c['set'] != 0: continue
        for j in range(c.get('count') or 1):
            for o in (0, 128): out[o + c['reg'] + j] = c['name']
    return out


def try_translate(blob):
    """Prova tutte le permutazioni (per nome) dei bool. Ritorna lista di (perm, 'OK'|motivo)."""
    sh = XL.parse(blob)
    reg = {}
    def cfn(name, j, count):
        k = (name, j)
        if k not in reg: reg[k] = len(reg)
        return reg[k] if reg[k] < 200 else None
    samp_names = {c['reg']: c['name'] for c in sh.ctab if c['set'] == 3}
    sreg = {}
    def samp(name, cidx):
        n = samp_names.get(cidx, name)
        if n not in sreg: sreg[n] = len(sreg)
        return sreg[n]
    bn = bool_names(sh); names = sorted(set(bn.values()))
    res = []
    for combo in itertools.product((0, 1), repeat=min(len(names), 4)):
        bv = dict(zip(names, combo)); bools = {i: bv.get(n, 0) for i, n in bn.items()}
        try:
            t = xenos2sm3.translate(blob, cfn, bools=bools, samp=samp)
            sm3asm.encode(sm3asm.parse_text(t.text))
            res.append((bv, 'OK'))
        except xenos2sm3.Reject as e:
            res.append((bv, 'REJ ' + reason(e)))
        except Exception as e:
            res.append((bv, 'ERR ' + reason(repr(e))))
    return res


def ps_slots(lib):
    return [s for s in range(len(lib['slots'])) if lib['slots'][s] != 0xffffffff]


def ctab_sig(sh):
    names = collections.Counter((norm_name(c['name']), c['set']) for c in sh.ctab)
    counts = collections.Counter((norm_name(c['name']), c['set'], c.get('count')) for c in sh.ctab)
    regs = collections.Counter((norm_name(c['name']), c['set'], c['reg'], c.get('count')) for c in sh.ctab)
    return names, counts, regs


def norm_line(l):
    l = re.sub(r'\br\d+\b', 'r', l)
    return l


def classify_diff(la, lb):
    """Diff riga per riga dei testi Xenos (temp normalizzati). Ritorna Counter delle classi delle righe diverse."""
    na, nb = [norm_line(x) for x in la], [norm_line(x) for x in lb]
    sm = difflib.SequenceMatcher(None, na, nb, autojunk=False)
    cnt = collections.Counter()
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal': continue
        A, B = na[i1:i2], nb[j1:j2]
        if tag != 'replace' or len(A) != len(B):
            cls = 'luci' if any(LIGHTRX.search(x) for x in A + B) else 'strut'
            cnt[cls] += max(len(A), len(B)); continue
        for a, b in zip(A, B):
            if LIGHTRX.search(a) or LIGHTRX.search(b): cnt['luci'] += 1; continue
            ra = re.sub(r'MaterialParams\[\d+\]\.[xyzw]+', 'MP', a); rb = re.sub(r'MaterialParams\[\d+\]\.[xyzw]+', 'MP', b)
            if ra == rb: cnt['MP'] += 1; continue
            da = re.sub(r'\bc\d+\.[xyzw]+|\bc\d+\b', 'C', ra); db = re.sub(r'\bc\d+\.[xyzw]+|\bc\d+\b', 'C', rb)
            if da == db: cnt['def'] += 1; continue
            cnt['strut'] += 1
    return cnt, sm.ratio()


def worst(cnt):
    for k in ('strut', 'luci', 'MP', 'def'):
        if cnt.get(k): return k
    return 'uguale'


def main():
    L = libs(); X, P, D, DM = L['X'], L['P'], L['D'], L['DM']
    rev = collections.defaultdict(list)
    for x, p in x2p().items(): rev[p].append(x)
    rows = list(csv.DictReader(open(os.path.join(HERE, 'illuminati.tsv')), delimiter='\t'))
    tsv = [('id_dlc', 'classe', 'pc_surrogato', 'gemello_xbox', 'ctab_nomi', 'ctab_count', 'ctab_reg', 'def_uguali', 'diff_def', 'diff_MP',
            'diff_luci', 'diff_strut', 'classe_diff', 'sim', 'traduz_dlc', 'drm')]
    hist_dlc = collections.Counter(); hist_base = collections.Counter(); cls_count = collections.Counter(); libcls = {}
    for r in rows:
        dl, pc = int(r['id_xbox']), int(r['id_pc_surrogato']); lib = D[dl]
        # (a)
        tr_tags = collections.Counter()
        for s in ps_slots(lib):
            for bv, t in try_translate(lib['entries'][lib['slots'][s]]['blob']):
                hist_dlc[t] += 1; tr_tags[t.split(' ')[0]] += 1
        # (c) gemello: fra le lib Xbox base che mappano sul surrogato PC, quella con firma CTAB piu' vicina
        shd = XL.parse(lib['entries'][lib['slots'][0]]['blob']); sd = ctab_sig(shd); ld = XL.text(shd, 'pretty').lines
        best = None
        for xt in rev.get(pc, []):
            if X[xt]['kind'] != lib['kind']: continue
            shx = XL.parse(X[xt]['entries'][X[xt]['slots'][0]]['blob']); sx = ctab_sig(shx)
            score = (sd[0] == sx[0], sd[1] == sx[1], sd[2] == sx[2])
            if best is None or score > best[0]: best = (score, xt, shx, sx)
        if best is None:
            tsv.append((dl, r['classe'], pc, '-', '', '', '', '', '', '', '', '', 'nogemello', '', dict(tr_tags), r['drm'])); libcls[dl] = 'nogemello'
            cls_count['nogemello'] += 1; continue
        score, xt, shx, sx = best
        lx = XL.text(shx, 'pretty').lines
        cnt, ratio = classify_diff(ld, lx)
        defs_eq = sorted(shd.defs.items()) == sorted(shx.defs.items())
        if not score[0]: cls = 'ctab_diversa'
        else: cls = worst(cnt)
        cls_count[cls] += 1; libcls[dl] = cls
        tsv.append((dl, r['classe'], pc, xt, int(score[0]), int(score[1]), int(score[2]), int(defs_eq), cnt.get('def', 0), cnt.get('MP', 0),
                    cnt.get('luci', 0), cnt.get('strut', 0), cls, '%.3f' % ratio, dict(tr_tags), r['drm']))
    # (b) coppie base illuminate pos2 con gemello PC
    pos = positions(); nbase = 0; base_ok_libs = 0
    for x, p in sorted(x2p().items()):
        if X[x]['kind'] != 1 or 2 not in pos.get(x, set()): continue
        sh0 = XL.parse(X[x]['entries'][X[x]['slots'][0]]['blob'])
        if not any(LIGHTRX.search(c['name']) for c in sh0.ctab): continue
        nbase += 1; any_ok = False
        for s in ps_slots(X[x]):
            for bv, t in try_translate(X[x]['entries'][X[x]['slots'][s]]['blob']):
                hist_base[t] += 1; any_ok |= t == 'OK'
        base_ok_libs += any_ok
    # (d) materiali con difetti
    dif = []
    for mid, why in DIFETTI.items():
        if mid not in DM: dif.append('- %d (%s): materiale non trovato fra i DLC' % (mid, why)); continue
        t = struct.unpack_from('>4I', DM[mid][0], 0x28)
        parts = ['pos%d=%d%s' % (i, t[i], '[ILL:%s]' % libcls[t[i]] if t[i] in libcls else '') for i in range(4) if t[i]]
        dif.append('- %d (%s): %s' % (mid, why, ' '.join(parts)))
    with open(OUT_TSV, 'w') as f:
        for row in tsv: f.write('\t'.join(str(c) for c in row) + '\n')
    md = ['# F5 censimento shader illuminati (generato da f5_census_lit.py)', '',
          '## (c) DLC vs gemello Xbox del surrogato: classe peggiore del diff (54 lib)',
          ', '.join('%s %d' % kv for kv in cls_count.most_common()),
          'Lettura: uguale/def/MP = correggibile con patch sul gemello PC senza tradurre le luci; luci/strut/ctab_diversa = serve traduzione o trapianto.', '',
          '## (d) materiali con difetti visibili -> lib (ILL = illuminata, classe)'] + dif + ['',
          '## (a) traduzione DLC illuminate (slot x permutazioni bool): motivi', ', '.join('%s: %d' % kv for kv in hist_dlc.most_common(8)), '',
          '## (b) oracolo base: %d lib illuminate pos2 con gemello PC, %d con almeno una permutazione traducibile' % (nbase, base_ok_libs),
          ', '.join('%s: %d' % kv for kv in hist_base.most_common(8)), '', 'Dettaglio per lib: f5_census_lit.tsv']
    open(OUT_MD, 'w').write('\n'.join(md) + '\n')
    print('\n'.join(md))


if __name__ == '__main__':
    main()
