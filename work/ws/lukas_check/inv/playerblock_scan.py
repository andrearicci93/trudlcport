"""playerblock_scan.py - (19/11/2026) SOLA LETTURA. Riscrittura (non import) della regola `playerblock` del fork di Lukas
(tools/player_block_fix.py, CHANGELOG 2026-11-10 K-5b): blocco dati player = bersaglio del puntatore DTP +0xc8 (PC
[0xfad764]), 0x1034 byte, s16 aria = 4000 a +0xf8; ogni parola nell'ordine byte che le coppie player base dimostrano.
LIMITE: la prova del fork usa 5 coppie base Xbox/PC (lara, lara_casual, lara_bikini, lara_wetsuit_cold, lara_snow_light);
gli archivi Xbox base (layer1/layer2) NON sono su questo PC e pairs.pkl e' vietato -> prova base NON eseguibile.
Al suo posto (dedotto, non prova base):
  (a) consenso interno: per ogni parola, l'insieme degli ordini byte Xbox->PC comune a tutti i blocchi B276 di layout
      Lara (costumi DLC1 + lara_doppelganger, tutti con blocco a +0x28f80) -> giudica gli altri (leave-one-out);
  (b) parole documentate dal fork per doppelganger_casual DTP 20212: +0x294 (4 u8, tempo lock LT: deve restare grezza,
      lettori movzx byte), +0x25c (coppia u16), +0x2a8 / +0x320 (id DTP suono), +0x70c (id oggetto u16), +0x1030 (aperta);
      stampate con Xbox, B276 e il PC base lara.drm DTP 850 (pc/bigfile.000) come riferimento di valore.
uso: python -I -B playerblock_scan.py [BASELINE] -> playerblock_<tag>.log accanto allo script"""
import sys, os, struct, collections
sys.path.insert(0, '/path/to/trudlcport/tools')
import drm_write as DW, drm_reloc as R
from archive import Archive
from dlc_names import PACKS, fcrc
from names import crc
BL = sys.argv[1] if len(sys.argv) > 1 else 'B276_scriptclash'
B = '/path/to/trudlcport/work/baseline/%s/mods/' % BL
TAG = BL.split('_')[0]
HERE = '/path/to/trudlcport/work/ws/lukas_check/inv/'
LOG = open(HERE + 'playerblock_%s.log' % TAG, 'w', encoding='utf-8')
def out(*a):
    s = ' '.join(str(x) for x in a); print(s); LOG.write(s + '\n')
BS = chr(92); LEN = 0x1034; AIR = 4000
ORDERS = {'same': (0, 1, 2, 3), 'u32': (3, 2, 1, 0), 'u16': (1, 0, 3, 2), 'b2s16': (0, 1, 3, 2), 's16b2': (1, 0, 2, 3)}
def apply(w, o): return bytes(w[i] for i in ORDERS[o])
def orders_of(x, p): return {n for n in ORDERS if apply(x, n) == p}
A = {p: Archive(PACKS[p], 'be') for p in ('pack11', 'pack10', 'pack1', 'pack2')}
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
XL = objlist('/path/to/trudlcport/work/generic/lists/dlc_pack11_objectlist.txt')
PL = objlist(B + 'tr8/pc-w/objectlist.txt')

def block(D, e):
    f = '>' if e == 'be' else '<'
    for k, s in enumerate(D.sections):
        if s.type != 7 or not s.reloc or len(s.data) < 0xcc: continue
        r = R.parse(bytes(s.reloc), e); t = dict(r.internal).get(0xc8)
        if t is None or t + LEN > len(s.data): continue
        if struct.unpack_from(f + 'h', s.data, t + 0xf8)[0] != AIR: continue
        nxt = [b for _, b in r.internal if b > t]
        if (min(nxt) if nxt else len(s.data)) - t != LEN: continue
        slots = {o - t for o in set(r.pointer_offsets()) | set(r.id_offsets()) if t <= o < t + LEN}
        d = s.data
        return dict(k=k, id=s.id, t=t, w=[bytes(d[t + o:t + o + 4]) for o in range(0, LEN, 4)], slots=slots)
    return None

# PC base lara.drm (riferimento di valore, non di ordine)
pcbig = Archive('/path/to/trudlcport/pc/bigfile.000', 'le')
rs = pcbig.find(crc('pc-w' + BS + 'lara.drm')); r = ([x for x in rs if x['spec'] == 0xffffffff] or rs)[-1]
LARA = block(DW.read(pcbig.read(r), 'le'), 'le')
out('PC base lara.drm: blocco DTP %d +0x%x' % (LARA['id'], LARA['t']))

files = []; NOX = []
for root, _, fs in os.walk(B):
    for f in sorted(fs):
        if not f.endswith('.drm'): continue
        rel = os.path.relpath(os.path.join(root, f), B).replace(BS, '/')
        PD = DW.read(open(os.path.join(root, f), 'rb').read(), 'le')
        bp = block(PD, 'le')
        if bp is None: continue
        xs = xbox(rel)
        bx = None; pk = None
        for p, raw in xs.items():
            b = block(DW.read(raw, 'be'), 'be')
            if b is not None and b['t'] == bp['t']: bx, pk = b, p; break
        grp = 'DLC1' if pk == 'pack10' else 'DLC2' if pk == 'pack11' else ('costumi_' + pk) if pk else 'no_xbox'
        out('%-6s %-32s Xbox %s, blocco DTP %d +0x%x' % (grp, rel, pk or '-', bp['id'], bp['t']))
        if bx is None: NOX.append((rel, bp, PD)); continue
        files.append(dict(rel=rel, grp=grp, x=bx, p=bp, PD=PD))
# file senza sorgente Xbox propria (es. dlc_doppel_costume_a = copia nostra): Xbox preso dal file con lo stesso DTP blocco
for rel, bp, PD in NOX:
    tw = [F for F in files if F['p']['id'] == bp['id'] and F['p']['t'] == bp['t']]
    if tw:
        out('%s: senza Xbox proprio, uso lo Xbox di %s (stesso DTP %d)' % (rel, tw[0]['rel'], bp['id']))
        files.append(dict(rel=rel, grp=tw[0]['grp'] + '_copia', x=tw[0]['x'], p=bp, PD=PD))

# classi d'ordine per file
out('')
for F in files:
    c = collections.Counter()
    for i in range(LEN // 4):
        o = 4 * i
        if o in F['x']['slots'] or o in F['p']['slots']: c['slot'] += 1; continue
        x, p = F['x']['w'][i], F['p']['w'][i]
        s = orders_of(x, p)
        c['same' if 'same' in s else (sorted(s)[0] if s else 'other')] += 1
    out('ordini %-30s %s' % (F['rel'], dict(sorted(c.items()))))

# (a) consenso interno leave-one-out sui blocchi di layout Lara (DTP != 20212)
REF = [F for F in files if F['p']['id'] != 20212]
out('\nriferimento consenso: %s' % ', '.join(F['rel'] for F in REF))
tot = collections.defaultdict(collections.Counter); bad_files = collections.defaultdict(set)
for F in files:
    others = [G for G in REF if G is not F]
    rows = []
    for i in range(LEN // 4):
        o = 4 * i
        if o in F['x']['slots'] or o in F['p']['slots'] or any(o in G['x']['slots'] or o in G['p']['slots'] for G in others):
            tot[F['grp']]['slot'] += 1; continue
        S = set(ORDERS); ok = True
        for G in others:
            s = orders_of(G['x']['w'][i], G['p']['w'][i])
            if not s: ok = False; break
            S &= s
        x, p = F['x']['w'][i], F['p']['w'][i]
        if not ok or not S: tot[F['grp']]['indeciso'] += 1; continue
        wants = {apply(x, n) for n in S}
        if len(wants) != 1:
            tot[F['grp']]['ok' if p in wants else 'ambiguo'] += 1
            if p not in wants: rows.append((o, x, p, None, 'ambiguo', '/'.join(sorted(S))))
            continue
        w = next(iter(wants))
        if p == w: tot[F['grp']]['ok'] += 1; continue
        od = orders_of(x, p)
        st = ('difforme:' + sorted(od)[0]) if od else 'altro'
        tot[F['grp']][st.split(':')[0]] += 1; bad_files[F['grp']].add(F['rel'])
        rows.append((o, x, p, w, st, '/'.join(sorted(S))))
    for o, x, p, w, st, why in rows:
        out('   %s +0x%03x Xbox %s B276 %s atteso %s [%s] PClara %s' % (F['rel'], o, x.hex(), p.hex(), w.hex() if w else '-', st + ' ' + why, LARA['w'][o // 4].hex()))

# (b) parole documentate dal fork
out('\nparole documentate dal fork (doppelganger_casual DTP 20212):')
def u16pair(b, e): return struct.unpack(e + 'HH', b)
DOC = collections.defaultdict(collections.Counter); DOCF = collections.defaultdict(set)
for F in files:
    if F['p']['id'] != 20212: continue
    secs = F['PD'].sections; ids7 = {s.id for s in secs if s.type == 7}
    for o, what in ((0x294, '4 u8, LT lock time = byte +0x294; atteso grezzo 08 00 05 00 (READERS movzx byte)'),
                    (0x25c, 'coppia u16 (fork: scambiata come u32)'), (0x2a8, 'id DTP suono (fork: Xbox 1163 -> PC 964)'),
                    (0x320, 'id DTP suono (fork: Xbox 1164 -> PC 965)'), (0x70c, 'id oggetto u16 (fork: Xbox 68 -> PC 52)'),
                    (0x1030, 'aperta nel fork (base 60 -> 64, DLC2 62)')):
        x, p = F['x']['w'][o // 4], F['p']['w'][o // 4]
        extra = ''
        if o in (0x2a8, 0x320):
            xv = struct.unpack('>I', x)[0]; pv = struct.unpack('<I', p)[0]
            extra = 'Xbox u32 %d, B276 u32 %d, sezione DTP %d nel PC: %s, DTP %d nel PC: %s' % (xv, pv, pv, pv in ids7, xv, xv in ids7)
        if o == 0x70c:
            xa = u16pair(x, '>'); pa = u16pair(p, '<')
            extra = 'Xbox u16 %s (%s), B276 u16 %s (%s)' % (xa, [XL.get(v) for v in xa], pa, [PL.get(v) for v in pa])
        slot = 'SLOT' if (o in F['x']['slots'] or o in F['p']['slots']) else ''
        if o == 0x294: v = 'OK' if p == x else 'DIFFORME'
        elif o == 0x25c: v = 'OK' if p == apply(x, 'u16') else 'DIFFORME'
        elif o in (0x2a8, 0x320): v = 'OK' if (pv != xv and pv in ids7) else 'DIFFORME'
        elif o == 0x70c:
            n = XL.get(xa[0]); ids = [i for i, m in PL.items() if m == n]
            v = 'OK' if (len(ids) == 1 and pa[0] == ids[0]) else 'DIFFORME (atteso u16 %s)' % ids
        else: v = 'aperta'
        DOC[F['grp']][v.split(' ')[0]] += 1
        if v.startswith('DIFF'): DOCF[F['grp']].add(F['rel'])
        out('  %-28s +0x%03x Xbox %s B276 %s PClara %s ordini %s %s => %s | %s %s' % (F['rel'], o, x.hex(), p.hex(), LARA['w'][o // 4].hex(),
            sorted(orders_of(x, p)) or 'nessuno', slot, v, what, extra))
out('')
for g, c in tot.items():
    out('TOTALE %s (consenso interno, dedotto): file difformi %d, %s' % (g, len(bad_files[g]), dict(sorted(c.items()))))
for g, c in DOC.items():
    out('TOTALE %s parole documentate dal fork (regola applicata come documentata): file difformi %d %s, %s' % (
        g, len(DOCF[g]), sorted(DOCF[g]), dict(sorted(c.items()))))
out('NB: prova base del fork (5 coppie Xbox/PC) NON eseguita: archivi Xbox base assenti, pairs.pkl vietato.')
LOG.close()
