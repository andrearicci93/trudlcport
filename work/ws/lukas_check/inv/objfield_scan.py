"""objfield_scan.py - (19/11/2026) SOLA LETTURA. Riscrittura (non import) della regola `objfield` del fork di Lukas
(tools/object_id_field_fix.py, CHANGELOG 2026-11-12 Q110): id oggetto u16 lasciati col valore Xbox.
Classi di campo (stesse del fork):
  GEAR   liste equipaggiamento di default della unit: sezione 0 (Level) +0x70 -> blocco env, env +0x2b4 -> {u32 DTP id A,
         u32 DTP id B}; ogni DTP lista {+0 u16* armi, +4 n, +8 u16* gear, +0xc n}; ogni voce = id oggetto.
  CHUNK  dati oggetto chunkdoll: DTP +0xc8 -> D con D+2 u16 = 0x3b e D+4 u16 = 0xb00b; D+8 u16 = id oggetto creatura.
Regola: campo PC (LE u16) = id PC del NOME dell'oggetto Xbox (lista oggetti Xbox del pack -> objectlist.txt PC della
baseline). Stato: ok / fix (PC tiene ancora l'id Xbox) / unmapped (nome assente o ambiguo) / UNEXPECTED (altro valore).
Accoppiamento Xbox/PC dei campi per classe e ordine, offset nella sezione uguali (come il fork).
La prova base del fork (81 unit / 1466 voci / 3 chunkdoll) usa pairs.pkl: NON eseguita qui (vietato caricarlo).
Gruppo: pack10 solo = DLC1, pack11 solo = DLC2, in entrambi = 'comune' (valutato su entrambi i pack, tenuto il migliore).
uso: python -I -B objfield_scan.py [BASELINE]   (default B276_scriptclash) -> objfield_<tag>.log accanto allo script"""
import sys, os, struct, collections
sys.path.insert(0, '/path/to/trudlcport/tools')
import drm_write as DW, drm_reloc as R
from archive import Archive
from dlc_names import PACKS, fcrc
BL = sys.argv[1] if len(sys.argv) > 1 else 'B276_scriptclash'
B = '/path/to/trudlcport/work/baseline/%s/mods/' % BL
TAG = BL.split('_')[0]
HERE = '/path/to/trudlcport/work/ws/lukas_check/inv/'
LOG = open(HERE + 'objfield_%s.log' % TAG, 'w', encoding='utf-8')
def out(*a):
    s = ' '.join(str(x) for x in a); print(s); LOG.write(s + '\n')
BS = chr(92)
A = {p: Archive(PACKS[p], 'be') for p in ('pack11', 'pack10')}
IDX = {p: {r['hash']: r for r in a.idx} for p, a in A.items()}
def xbox(rel):
    h = fcrc('xenon-w' + BS + rel.replace('/', BS))
    return {p: A[p].read(IDX[p][h]) for p in A if h in IDX[p]}
def objlist(path):
    d = {}
    for line in open(path, encoding='utf-8', errors='replace').read().splitlines()[1:]:
        if ',' in line:
            i, n = line.split(',', 1); d[int(i)] = n.strip().lower()
    return d
XL = {p: objlist('/path/to/trudlcport/work/generic/lists/dlc_%s_objectlist.txt' % p) for p in A}
PL = objlist(B + 'tr8/pc-w/objectlist.txt')
PBYNAME = collections.defaultdict(list)
for i, n in PL.items(): PBYNAME[n].append(i)
def pc_id(xid, pack):
    n = XL[pack].get(xid)
    if n is None: return None
    ids = PBYNAME.get(n, [])
    return ids[0] if len(ids) == 1 else None

class Img:
    def __init__(self, D, e):
        self.D = D; self.E = '>' if e == 'be' else '<'; self.ptr = []
        self.dtp = {s.id: i for i, s in enumerate(D.sections) if s.type == 7}
        for i, s in enumerate(D.sections):
            r = R.parse(bytes(s.reloc), e) if s.reloc else R.Reloc()
            m = {o: (i, t) for o, t in r.internal}
            for si, src, dst in r.external: m[src] = (si, dst)
            self.ptr.append(m)
    def deref(self, loc, off):
        return self.ptr[loc[0]].get(loc[1] + off) if loc else None
    def u32(self, loc, off):
        return struct.unpack_from(self.E + 'I', self.D.sections[loc[0]].data, loc[1] + off)[0]
    def u16(self, k, o):
        return struct.unpack_from(self.E + 'H', self.D.sections[k].data, o)[0]

def fields(img):
    res = []; D = img.D
    if D.sections and D.sections[0].type == 0:
        try: g = img.deref(img.deref((0, 0), 0x70), 0x2b4)
        except Exception: g = None
        if g is not None:
            seen = set()
            for tag, k in (('A', 0), ('B', 4)):
                did = img.u32(g, k)
                if did not in img.dtp or did in seen: continue
                seen.add(did); p = (img.dtp[did], 0)
                for kind, h in (('weapon', 0), ('gear', 8)):
                    q = img.deref(p, h); n = img.u32(p, h + 4)
                    if q is None or n > 64 or q[0] != p[0]: continue
                    for i in range(n):
                        res.append(('GEAR', q[0], q[1] + 2 * i, 'lista %s DTP %d %s[%d]' % (tag, did, kind, i)))
    for i, s in enumerate(D.sections):
        if s.type != 7: continue
        t = img.ptr[i].get(0xc8)
        if t is None or t[0] != i or t[1] + 0x10 > len(s.data): continue
        if img.u16(i, t[1] + 2) == 0x3b and img.u16(i, t[1] + 4) == 0xb00b:
            res.append(('CHUNK', i, t[1] + 8, 'chunkdoll DTP %d +0x%x D+8' % (s.id, t[1])))
    return res

def plan(XD, PD, pack):
    xi, pi = Img(XD, 'be'), Img(PD, 'le')
    xf, pf = fields(xi), fields(pi)
    rows, miss = [], []
    for cl in ('GEAR', 'CHUNK'):
        a = [f for f in xf if f[0] == cl]; b = [f for f in pf if f[0] == cl]
        if len(a) != len(b) or any(f[2] != g[2] for f, g in zip(a, b)):
            if a or b: miss.append('%s: Xbox %d campi, PC %d (offset diversi)' % (cl, len(a), len(b)))
            continue
        for f, g in zip(a, b):
            xv = xi.u16(f[1], f[2]); pv = pi.u16(g[1], g[2])
            want = pc_id(xv, pack) if xv not in (0, 0xffff) else xv
            st = 'unmapped' if want is None else 'ok' if pv == want else 'fix' if pv == xv else 'UNEXPECTED'
            rows.append((cl, PD.sections[g[1]].id, g[2], xv, pv, want, st, g[3], XL[pack].get(xv), PL.get(pv)))
    return rows, miss

tot = collections.defaultdict(collections.Counter); files_bad = collections.defaultdict(set); nfiles = collections.Counter()
for root, _, fs in os.walk(B):
    for f in sorted(fs):
        if not f.endswith('.drm'): continue
        rel = os.path.relpath(os.path.join(root, f), B).replace(BS, '/')
        PD = DW.read(open(os.path.join(root, f), 'rb').read(), 'le')
        if not fields(Img(PD, 'le')): continue
        xs = xbox(rel)
        grp = 'DLC1' if list(xs) == ['pack10'] else 'DLC2' if list(xs) == ['pack11'] else 'comune' if xs else 'no_xbox'
        nfiles[grp] += 1
        if not xs: out('NOXBOX', rel); continue
        best = None
        for pk, raw in xs.items():
            rows, miss = plan(DW.read(raw, 'be'), PD, pk)
            score = (-len(miss), -sum(r[6] != 'ok' for r in rows))
            if best is None or score > best[0]: best = (score, pk, rows, miss)
        _, pk, rows, miss = best
        for m in miss: out('NONACCOPPIATO', grp, rel, pk, m)
        c = collections.Counter(r[6] for r in rows)
        out('%-6s %-45s %s campi %d %s' % (grp, rel, pk, len(rows), dict(c)))
        for r in rows:
            tot[grp][(r[0], r[6])] += 1
            if r[6] != 'ok': files_bad[grp].add(rel)
            if r[6] != 'ok' or r[0] == 'CHUNK':
                out('   %s %s DTP %d +0x%x Xbox %d (%s) PC %d (%s) atteso %s (%s)' % (r[6], r[0], r[1], r[2], r[3], r[8], r[4], r[9], r[5], r[7]))
out('')
for g in ('DLC1', 'DLC2', 'comune', 'no_xbox'):
    if nfiles[g]:
        out('TOTALE %s: file con campi %d, file difformi %d, parole %s' % (g, nfiles[g], len(files_bad[g]),
            ', '.join('%s %s %d' % (k[0], k[1], v) for k, v in sorted(tot[g].items()))))
out('NB: prova base del fork (pairs.pkl) non eseguita; regola applicata come documentata.')
LOG.close()
