"""navraw_scan.py - (19/11/2026) SOLA LETTURA. Riscrittura (non import) della regola `navraw` del fork di Lukas
(tools/navgraph_raw_fix.py, finding 50, CHANGELOG 2026-11-06): l'immagine NavPower NavGraph della unit (Level+0x60,
sezione tipo 0 id 0, senza rilocazioni) deve essere = byte Xbox, tranne la parola COUNT dopo la risorsa 1 scambiata u32.
Layout: +0 ffffffff, risorsa 1 {u32 0, u32 1, u32 size, u32 checksum, size byte}, u32 COUNT (ordine piattaforma),
COUNT risorse; tutto little-endian su entrambe le piattaforme salvo COUNT.
Confronto anche con la NOSTRA regola tools/navmesh_fix.py (sezione = byte Xbox, parola [Level+0x68] scambiata s32):
si verifica se Level+0x68 punta proprio alla parola COUNT (stessa regola) o altrove.
La prova base del fork (82 coppie) usa archivi Xbox base assenti / pairs.pkl vietato: NON eseguita.
uso: python -I -B navraw_scan.py [BASELINE] -> navraw_<tag>.log accanto allo script"""
import sys, os, struct, collections
sys.path.insert(0, '/path/to/trudlcport/tools')
import drm_write as DW, drm_reloc as R
from archive import Archive
from dlc_names import PACKS, fcrc
BL = sys.argv[1] if len(sys.argv) > 1 else 'B276_scriptclash'
B = '/path/to/trudlcport/work/baseline/%s/mods/' % BL
TAG = BL.split('_')[0]
HERE = '/path/to/trudlcport/work/ws/lukas_check/inv/'
LOG = open(HERE + 'navraw_%s.log' % TAG, 'w', encoding='utf-8')
def out(*a):
    s = ' '.join(str(x) for x in a); print(s); LOG.write(s + '\n')
BS = chr(92)
PERMS = {'u32': (3, 2, 1, 0), 'u16u16': (1, 0, 3, 2), 'u8u8u16': (0, 1, 3, 2), 'u16u8u8': (1, 0, 2, 3), 'halves': (2, 3, 0, 1)}
A = {p: Archive(PACKS[p], 'be') for p in ('pack11', 'pack10')}
IDX = {p: {r['hash']: r for r in a.idx} for p, a in A.items()}
def xbox(rel):
    h = fcrc('xenon-w' + BS + rel.replace('/', BS))
    return {p: A[p].read(IDX[p][h]) for p in A if h in IDX[p]}
def word_class(w, p):
    if p == w: return 'ok'
    for n, o in PERMS.items():
        if bytes(w[i] for i in o) == p: return n
    return 'other'

def image(D, e):
    """dict(sec, off, b2 = offset di [Level+0x68] nella stessa sezione o None, ...) o None"""
    if not D.sections or D.sections[0].type != 0: return None
    r0 = R.parse(bytes(D.sections[0].reloc), e)
    ext = {so: (si, do) for si, so, do in r0.external}
    if not (0 in ext and len(D.sections[ext[0][0]].data) == 24): return None
    it = dict(r0.internal)
    loc = ext.get(0x60) or ((0, it[0x60]) if 0x60 in it else None)
    if loc is None: return None
    si, o = loc; s = D.sections[si]
    b2 = ext.get(0x68) or ((0, it[0x68]) if 0x68 in it else None)
    return dict(sec=si, off=o, len=len(s.data) - o, type=s.type, id=s.id, reloc_empty=R.parse(bytes(s.reloc), e).empty(),
                b2=(b2[1] - o) if b2 and b2[0] == si else None, data=bytes(s.data)[o:])

def resources(d, E):
    if len(d) < 4 or d[:4] != b'\xff\xff\xff\xff': return [], None, d == b'\0' * len(d)
    def res(r):
        if r + 0x14 > len(d): return None
        z, one, size, chk, kind = struct.unpack_from('<5I', d, r)
        end = r + 0x10 + size
        return None if (z != 0 or one != 1 or size < 4 or end > len(d)) else (r, size, kind, end)
    r1 = res(4)
    if r1 is None or r1[3] + 4 > len(d): return ([r1] if r1 else []), None, False
    outl = [r1]; cq = r1[3]; n = struct.unpack_from(E + 'I', d, cq)[0]; r = cq + 4
    if n > 64: return outl, cq, False
    for _ in range(n):
        x = res(r)
        if x is None: return outl, cq, False
        outl.append(x); r = x[3]
    return outl, cq, r == len(d)

def plan(XD, PD):
    xi, pi = image(XD, 'be'), image(PD, 'le')
    if xi is None and pi is None: return dict(status='no image')
    if xi is None or pi is None: return dict(status='immagine da un lato solo (Xbox %s, PC %s)' % (xi is not None, pi is not None))
    why = [k for k in ('sec', 'off', 'len', 'type', 'id') if xi[k] != pi[k]]
    if why: return dict(status='layout diverso (%s)' % ', '.join('%s X %s P %s' % (k, xi[k], pi[k]) for k in why), xi=xi, pi=pi)
    if not (xi['reloc_empty'] and pi['reloc_empty']): return dict(status='sezione con rilocazioni', xi=xi, pi=pi)
    xd, pd = xi['data'], pi['data']
    if len(xd) % 4: return dict(status='lunghezza non multipla di 4', xi=xi, pi=pi)
    rs, cq, covers = resources(xd, '>')
    if not covers: return dict(status='catena risorse non copre l immagine (%d)' % len(rs), xi=xi, pi=pi)
    w = bytearray(xd)
    if cq is not None: w[cq:cq + 4] = xd[cq:cq + 4][::-1]
    rows = []; cls = collections.Counter()
    for q in range(0, len(xd), 4):
        c = word_class(bytes(w[q:q + 4]), pd[q:q + 4]); cls[c] += 1
        if c != 'ok': rows.append((q, bytes(w[q:q + 4]), pd[q:q + 4], c))
    return dict(status='ok', rows=rows, cls=cls, cq=cq, nres=len(rs), xi=xi, pi=pi, words=len(xd) // 4)

tot = collections.defaultdict(collections.Counter); bad = collections.defaultdict(list)
for root, _, fs in os.walk(B):
    for f in sorted(fs):
        if not f.endswith('.drm'): continue
        rel = os.path.relpath(os.path.join(root, f), B).replace(BS, '/')
        PD = DW.read(open(os.path.join(root, f), 'rb').read(), 'le')
        if image(PD, 'le') is None: continue
        xs = xbox(rel)
        grp = 'DLC1' if list(xs) == ['pack10'] else 'DLC2' if list(xs) == ['pack11'] else 'comune' if xs else 'no_xbox'
        tot[grp]['unit'] += 1
        if not xs: out('%-6s %-36s nessuna sorgente Xbox' % (grp, rel)); continue
        best = None
        for pk, raw in xs.items():
            info = plan(DW.read(raw, 'be'), PD)
            sc = (info['status'] == 'ok', -len(info.get('rows', [])))
            if best is None or sc > best[0]: best = (sc, pk, info)
        _, pk, info = best
        if info['status'] != 'ok':
            tot[grp]['non_confrontabile'] += 1; out('%-6s %-36s %s: NON CONFRONTABILE %s' % (grp, rel, pk, info['status'])); continue
        xi = info['xi']; cq = info['cq']
        same68 = 'b2=COUNT' if xi['b2'] == cq else ('b2 +%s COUNT +%s' % (hex(xi['b2']) if xi['b2'] is not None else None, hex(cq) if cq is not None else None))
        cl = collections.Counter(r[3] for r in info['rows'])
        for k, v in cl.items(): tot[grp]['parole_' + k] += v
        tot[grp]['parole'] += info['words']
        cnt = xi['data'][cq:cq + 4].hex() + '->' + info['pi']['data'][cq:cq + 4].hex() if cq is not None else '-'
        out('%-6s %-36s %s sez %d +0x%x %d byte, %d risorse, COUNT %s [%s]: %s' % (grp, rel, pk, xi['sec'], xi['off'], xi['len'],
            info['nres'], cnt, same68, 'grezza (0 difformi)' if not info['rows'] else '%d DIFFORMI %s primi %s' % (
                len(info['rows']), dict(cl), ' '.join('+%#x:%s>%s' % (q, a.hex(), b.hex()) for q, a, b, c in info['rows'][:4]))))
        if info['rows']: bad[grp].append((rel, len(info['rows'])))
out('')
for g, c in tot.items():
    out('TOTALE %s: %s; unit difformi %d %s' % (g, dict(sorted(c.items())), len(bad[g]), bad[g]))
out('NB: prova base del fork (82 coppie base) NON eseguita; regola applicata come documentata.')
LOG.close()
