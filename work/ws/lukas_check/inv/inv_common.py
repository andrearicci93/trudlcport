"""inv_common.py - (19/11/2026) helper SOLO LETTURA per gli scan di verifica dei passi del fork di Lukas.
Nessuna scrittura fuori da questa cartella; nessun codice del fork importato (logica riscritta).
- files(base): [(rel, path)] dei DRM della baseline
- xbox(rel): bytes del DRM Xbox (pack11, poi pack10) o None
- pc_generalbank(): sezioni del generalbank.drm PC originale (patch.000, altrimenti bigfile.000)
- idmap(): work/generic/idmap.json (tipo -> {xbox id: pc id}; '100' = Symbol)
- locmap(): work/generic/locals/locmap_xbox_to_pc.json (indice stringa Xbox -> PC)"""
import sys, os, json, struct
sys.path.insert(0, '/path/to/trudlcport/tools')
import drm_write as DW, drm_reloc as R
from archive import Archive
from dlc_names import PACKS, fcrc
BS = chr(92)
_A = None


def base_dir(name):
    return '/path/to/trudlcport/work/baseline/%s/mods/' % name


def files(name):
    B = base_dir(name); out = []
    for root, _, fs in os.walk(B):
        for f in sorted(fs):
            if f.endswith('.drm'):
                p = os.path.join(root, f)
                out.append((os.path.relpath(p, B).replace(BS, '/'), p))
    return sorted(out)


def xbox(rel):
    global _A
    if _A is None: _A = [(p, Archive(PACKS[p], 'be')) for p in ('pack11', 'pack10')]
    h = fcrc('xenon-w' + BS + rel.replace('/', BS))
    for p, a in _A:
        rs = [r for r in a.idx if r['hash'] == h]
        if rs: return a.read(rs[0])
    return None


def xpack(rel):
    global _A
    if _A is None: _A = [(p, Archive(PACKS[p], 'be')) for p in ('pack11', 'pack10')]
    h = fcrc('xenon-w' + BS + rel.replace('/', BS))
    for p, a in _A:
        if any(r['hash'] == h for r in a.idx): return p
    return None


def pc_generalbank():
    h = fcrc('pc-w' + BS + 'generalbank.drm')
    for f in ('patch.000', 'bigfile.000'):
        a = Archive('/path/to/trudlcport/pc/' + f, 'le')
        rs = [r for r in a.idx if r['hash'] == h]
        if rs: return DW.read(a.read(rs[-1]), 'le').sections, f
    return None, None


_IM = None


def idmap():
    global _IM
    if _IM is None:
        d = json.load(open('/path/to/trudlcport/work/generic/idmap.json'))
        _IM = {int(t): {int(k): v for k, v in m.items()} for t, m in d.items()}
    return _IM


def locmap():
    d = json.load(open('/path/to/trudlcport/work/generic/locals/locmap_xbox_to_pc.json'))
    return {int(k): v for k, v in d['map'].items()}


def slots(reloc, e):
    r = R.parse(reloc, e)
    return set(r.pointer_offsets()) | set(r.id_offsets())


def pair_scripts(X, P):
    """coppie (sezione Xbox, sezione PC) tipo 8: id mappato (idmap tipo 8, id >= 20000 = stesso id o rinumerato) e stessa
    lunghezza; altrimenti unica sezione PC di pari lunghezza e stesso insieme di puntatori interni. -> (coppie, non accoppiate)"""
    im = idmap().get(8, {})
    pcs = [p for p in P if p.type == 8 and p.data]
    byid = {}
    for p in pcs: byid.setdefault(p.id, []).append(p)
    out, un, used = [], [], set()
    for x in X:
        if x.type != 8 or not x.data: continue
        nid = im.get(x.id, x.id)
        c = [p for p in byid.get(nid, []) + (byid.get(x.id, []) if nid != x.id else []) if len(p.data) == len(x.data) and id(p) not in used]
        if len(c) != 1:
            xi = sorted(R.parse(x.reloc, 'be').internal)
            c = [p for p in pcs if len(p.data) == len(x.data) and id(p) not in used and sorted(R.parse(p.reloc, 'le').internal) == xi]
        if len(c) == 1:
            used.add(id(c[0])); out.append((x, c[0]))
        else:
            un.append((x.id, len(c)))
    return out, un


def align(xd, pd):
    """{offset Xbox: offset PC} parola per parola. Stessa lunghezza: identita'. Altrimenti difflib sulle chiavi
    'multiinsieme dei 4 byte' (invariante all'ordine dei byte); blocchi 'replace' di pari lunghezza accoppiati in ordine."""
    if len(xd) == len(pd): return {o: o for o in range(0, len(xd) - 3, 4)}
    import difflib
    kx = [bytes(sorted(xd[o:o + 4])) for o in range(0, len(xd) - 3, 4)]
    kp = [bytes(sorted(pd[o:o + 4])) for o in range(0, len(pd) - 3, 4)]
    m = {}
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, kx, kp, autojunk=False).get_opcodes():
        if tag == 'equal' or (tag == 'replace' and i2 - i1 == j2 - j1):
            for k in range(i2 - i1): m[4 * (i1 + k)] = 4 * (j1 + k)
    return m


def pair_scripts_any(X, P):
    """come pair_scripts ma ammette lunghezze diverse (id mappato unico) -> [(x, p, mappa offset)], non accoppiate"""
    im = idmap().get(8, {})
    byid = {}
    for p in P:
        if p.type == 8 and p.data: byid.setdefault(p.id, []).append(p)
    out, un = [], []
    for x in X:
        if x.type != 8 or not x.data: continue
        c = byid.get(im.get(x.id, x.id), [])
        if len(c) != 1:
            same, u2 = pair_scripts([x], P)
            if same: out.append((same[0][0], same[0][1], align(x.data, same[0][1].data)))
            else: un.append((x.id, len(c)))
            continue
        out.append((x, c[0], align(x.data, c[0].data)))
    return out, un


class Log:
    def __init__(self, path):
        self.f = open(path, 'w', encoding='utf-8')

    def __call__(self, *a):
        t = ' '.join(str(x) for x in a)
        print(t); self.f.write(t + '\n'); self.f.flush()
