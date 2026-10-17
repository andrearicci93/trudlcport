"""template_rule.py - chiave 'modello' = (lunghezza DTP, insieme degli offset dei puntatori interni): coerenza per offset sulle coppie base e copertura sul DLC."""
import sys, os, collections, hashlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
import dtp_audit as DA, drm_write as DW, drm_reloc as R
PERMS = DA.PERMS; NAMES = DA.NAMES
def key_of(xd, xr):
    return (len(xd), hashlib.md5(repr(sorted(xr.internal)).encode()).hexdigest()[:10])
grp = collections.defaultdict(list); n = 0
for x, p, xb, pc, xr in DA.base_pairs():
    grp[key_of(xb['data'], xr)].append((xb['data'], pc['data'], xr)); n += 1
print('coppie base', n, 'modelli distinti', len(grp), 'modelli con >=2 coppie', sum(1 for v in grp.values() if len(v) >= 2))
cons = incons = words = 0
rules = {}
for k, v in grp.items():
    if len(v) < 2: continue
    L = k[0]
    for o in range(0, L - 3, 4):
        cs = None; ns = 0
        for xd, pd, xr in v:
            sl = set(xr.pointer_offsets()) | set(xr.id_offsets())
            if o in sl: cs = None; break
            c = DA.cls(xd[o:o + 4], pd[o:o + 4])
            if c in (0, DA.ALL): continue
            ns += 1
            cs = c if cs is None else (cs & c)
        if cs is None: continue
        words += 1
        if cs:
            cons += 1
            if ns >= 3 and bin(cs).count('1') == 1: rules[(k, o)] = cs
        else: incons += 1
print('parole-offset informative', words, 'coerenti', cons, 'incoerenti', incons, '(%.3f%% incoerenti)' % (100 * incons / max(1, words)))
# copertura DLC
import dtpid_sweep as DS
st, ids = DS.ctx(); basep = set(ids.base[7].values())
cov = tot = hit = 0; newdtp = 0
for rel, path in sorted(DA.overlay(['baseline/B31/mods'], None).items()):
    xs = DA.xsecs(rel)
    if xs is None: continue
    try: D = DW.read(open(path, 'rb').read(), 'le')
    except Exception: continue
    for x, i in DA.section_pairs(xs, D):
        sec = D.sections[i]
        if x['type'] != 7 or len(sec.data) != len(x['data']): continue
        xr = R.parse(x['reloc'], 'be'); k = key_of(x['data'], xr); newdtp += 1
        if k in grp and len(grp[k]) >= 2: cov += 1
print('DTP DLC totali', newdtp, 'con un modello presente (>=2 coppie) nel gioco base:', cov, '(%.1f%%)' % (100 * cov / max(1, newdtp)))

# ---- applicazione al DLC: parole il cui PC attuale NON e' consistente con la regola del modello
import json, struct
cand = []; ncheck = 0
for rel, path in sorted(DA.overlay(['baseline/B11/mods'], None).items()):
    xs = DA.xsecs(rel)
    if xs is None: continue
    try: D = DW.read(open(path, 'rb').read(), 'le')
    except Exception: continue
    for x, i in DA.section_pairs(xs, D):
        sec = D.sections[i]
        if x['type'] != 7 or len(sec.data) != len(x['data']): continue
        xd, pd = x['data'], sec.data; xr = R.parse(x['reloc'], 'be'); k = key_of(xd, xr)
        if k not in grp or len(grp[k]) < 2: continue
        sl = set(xr.pointer_offsets()) | set(xr.id_offsets())
        for o in range(0, len(xd) - 3, 4):
            r = rules.get((k, o))
            if r is None or o in sl: continue
            ncheck += 1
            c = DA.cls(xd[o:o + 4], pd[o:o + 4])
            if c in (0,) or (c & r): continue          # c==0: non e' una permutazione (id/rielaborato) ; c&r: coerente
            cand.append((rel, sec.id, o, xd[o:o + 4].hex(), pd[o:o + 4].hex(), [NAMES[j] for j in range(5) if r >> j & 1]))
print('parole controllate col modello', ncheck, '| candidati difetto', len(cand))
c = collections.Counter(a[0] for a in cand)
for f, v in c.most_common(25): print('%5d %s' % (v, f))
open('work/ws/progress/template_candidates_B11.tsv', 'w').write('file\tdtp\toff\txbox\tpc\tregola\n' + '\n'.join('%s\t%d\t0x%x\t%s\t%s\t%s' % (a[0], a[1], a[2], a[3], a[4], '/'.join(a[5])) for a in cand) + '\n')
