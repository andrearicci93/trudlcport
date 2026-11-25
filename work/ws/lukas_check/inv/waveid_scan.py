"""waveid_scan.py - (19/11/2026) SOLA LETTURA. Verifica del passo `waveid` del fork di Lukas
(tools/soundplex_wave_id_fix.py, logica riscritta qui, nessun suo codice importato).

Regola: DTP SoundPlex (parola 0 = nodo radice {u32 tipo 1..13, ptr interno}); dai nodi raggiungibili via puntatori figli,
le foglie Wave (tipo 2) hanno data+0 = id onda (nessuna reloc), data+4 = {u8, u8, u16}.
PC +0 = wavemap(x) se l'onda x e' una sezione tipo 6 del DRM stesso (coppia per posizione), altrimenti ids(6, x)
(idmap.json tipo 6, poi dlc_idmap.json 'new' 6, altrimenti x); 0/0xffffffff invariati.
PC +4 = parola Xbox con SOLO la meta' u16 scambiata (byte 0,1,3,2).
Alberi incorporati: liste eventi anim (u32 0, record {u16 h, s16 frame, ...}, fine 0xffff), record kind 0 (h&3==0, size>=16,
byte +8 == 0) con puntatore interno a +12 verso un nodo 1..13 = radice incorporata (solo se la parola 0 non e' radice).

Abbinamento sezioni Xbox/PC: difflib su (tipo, dimensione) come il fork; DTP usato solo se stessa dimensione e stessi
puntatori interni; DTP base rinumerato (id diverso e id Xbox in idmap tipo 7) = sezione del PC, saltato (contato).
Classi +0: ok | sbagliata:{dtp_id = ids(7,x), non_mappato = x, bswap, u16pair, altro}; per ogni sbagliata anche
'muta' (id PC non e' onda del DRM ne' onda base PC = valori idmap tipo 6) o 'altra_onda' (suona un'altra onda).
'ok_muta' = parola giusta ma bersaglio non trovato. Classi +4: ok | raw | u32 | u16u16 | altro.
In piu': scansione solo-PC di tutte le foglie (anche DTP saltati) -> riferimenti irrisolti; conteggio onde tipo 6 che
sono stub di silenzio (nome 'silence.wav', hash FSB zero, dati tutti zero).
uso: python -I -B waveid_scan.py [BASELINE]   (default B276_scriptclash) -> stampa; redirigere nel log"""
import sys, os, struct, collections, json, difflib
sys.path.insert(0, '/path/to/trudlcport/tools')
import drm_write as DW, drm_reloc as R
from archive import Archive
from dlc_names import PACKS, fcrc

BL = sys.argv[1] if len(sys.argv) > 1 else 'B276_scriptclash'
B = '/path/to/trudlcport/work/baseline/%s/mods/' % BL
BS = chr(92)
NULLS = (0, 0xffffffff)
MAX_ID = 0x10000
PACK_ORDER = ('pack11', 'pack10', 'pack1', 'pack2')
ALIAS = {'dlc_doppel_costume_a.drm': 'doppelganger_casual.drm'}   # clone del casual (oggetto 857->1031), nessun DRM Xbox proprio
DLC_OF = {'pack11': 'DLC2', 'pack10': 'DLC1', 'pack1': 'costumi', 'pack2': 'costumi'}

G = '/path/to/trudlcport/work/generic/'
_raw = json.load(open(G + 'idmap.json'))
BASE = {int(t): {int(a): b for a, b in d.items()} for t, d in _raw.items()}
NEW = {int(t): {int(a): b for a, b in d.items()} for t, d in json.load(open(G + 'dlc_idmap.json'))['new'].items()}
def ids(t, x):
    b = BASE.get(t, {})
    if x in b: return b[x]
    n = NEW.get(t, {})
    if x in n: return n[x]
    return x
BASE_PC_WAVES = set(BASE[6].values())

ARCH = {}
for p in PACK_ORDER:
    try: ARCH[p] = Archive(PACKS[p], 'be')
    except Exception as e: print('pack non disponibile', p, e)

def xbox_raws(rel):
    h = fcrc('xenon-w' + BS + rel.replace('/', BS))
    out = []
    for p, a in ARCH.items():
        rs = [r for r in a.idx if r['hash'] == h]
        if rs: out.append((p, a.read(rs[0])))
    return out

# ------------------------------------------------------------------ albero SoundPlex (entrambi gli ordini di byte)
def plex_nodes(d, rel, E):
    it = dict(rel.internal)
    slots = set(rel.pointer_offsets()) | set(rel.id_offsets())
    nd = {}
    for o, tg in rel.internal:
        if o < 4 or o % 4 or (o - 4) in slots or tg % 4 or tg + 4 > len(d): continue
        t = struct.unpack_from(E + 'I', d, o - 4)[0]
        if t > 13: continue
        nd[o - 4] = (t, tg)
    return nd, it, slots

def children(d, E, it, nd, off):
    t, tg = nd[off]
    out = []
    if t in (1, 2, 3): return out
    for o in range(tg, min(tg + 0x60, len(d)), 4):
        p = it.get(o)
        if p is None: continue
        if p in nd and p != off:
            out.append(p); continue
        for q in range(p, min(p + 0x100, len(d)), 4):      # array di puntatori a figli
            p2 = it.get(q)
            if p2 is None:
                if q > p + 8 and q + 4 <= len(d) and struct.unpack_from(E + 'I', d, q)[0] > 13: break
                continue
            if p2 in nd and p2 != off: out.append(p2)
        if t == 4: break                                    # Assign: solo +0 e' figlio
    return out

def evlist(d, E):
    if len(d) < 8 or d[:4] != b'\0\0\0\0': return None
    a = 4; out = []
    while a + 4 <= len(d):
        h, fr = struct.unpack_from(E + 'Hh', d, a)
        if h == 0xffff: return out or None
        sz = (h >> 12) * 4 + 8
        if fr < 0 or not 1 <= (h >> 12) <= 8 or a + sz > len(d): return None
        out.append((a, h, fr, sz)); a += sz
    return None

def wave_leaves(d, rel, e, max_id=MAX_ID):
    """-> (offsets data delle foglie Wave, 'root0'|'embedded'|None)"""
    E = '<' if e == 'le' else '>'
    nd, it, slots = plex_nodes(d, rel, E)
    roots, kind = [], None
    if len(d) >= 8 and 0 not in slots and 0 in nd and 1 <= nd[0][0] <= 13: roots, kind = [0], 'root0'
    elif len(d) >= 8:
        w = evlist(d, E)
        if w:
            rs = set()
            for a, h, fr, sz in w:
                if h & 3 or sz < 16 or d[a + 8] != 0: continue
                p = it.get(a + 12)
                if p is not None and p in nd and 1 <= nd[p][0] <= 13: rs.add(p)
            roots = sorted(rs)
            if roots: kind = 'embedded'
    if not roots: return [], None
    seen = set(); st = list(roots); out = []
    while st:
        off = st.pop()
        if off in seen: continue
        seen.add(off)
        t, tg = nd[off]
        if t == 2:
            if tg + 8 <= len(d) and tg not in slots and (tg + 4) not in slots:
                v = struct.unpack_from(E + 'I', d, tg)[0]
                if max_id is None or v in NULLS or v < max_id: out.append(tg)
            continue
        st += children(d, E, it, nd, off)
    return sorted(set(out)), kind

def bswap(v): return struct.unpack('<I', struct.pack('>I', v))[0]
def u16p(v):
    b = struct.pack('>I', v); return struct.unpack('<I', b[1::-1] + b[:1:-1])[0]
PERMS = {'raw': (0, 1, 2, 3), 'u32': (3, 2, 1, 0), 'u16u16': (1, 0, 3, 2), 'u8u8u16': (0, 1, 3, 2)}

def pairs(XS, PS):
    a = [(s.type, len(s.data)) for s in XS]; b = [(s.type, len(s.data)) for s in PS]
    out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == 'equal' or (tag == 'replace' and i2 - i1 == j2 - j1 and [t for t, _ in a[i1:i2]] == [t for t, _ in b[j1:j2]]):
            out += [(j1 + k, XS[i1 + k], PS[j1 + k]) for k in range(j2 - j1)]
    return out

def is_silence(d):
    d = bytes(d)
    return len(d) > 144 and d[16:20] == b'FSB4' and d[66:96].split(b'\0')[0] == b'silence.wav' and not any(d[144:])

# ------------------------------------------------------------------ passo 1: tutti i DRM, onde globali
files = []
for root, _, fs in os.walk(B):
    for f in sorted(fs):
        if f.lower().endswith('.drm'):
            files.append(os.path.relpath(os.path.join(root, f), B).replace(BS, '/'))
PCD = {}; ALL_WAVES = collections.defaultdict(set)
for rel in files:
    try: PCD[rel] = DW.read(open(B + rel, 'rb').read(), 'le').sections
    except Exception as e: print('ERR PC', rel, e); continue
    for s in PCD[rel]:
        if s.type == 6: ALL_WAVES[s.id].add(rel)

TOT = collections.defaultdict(collections.Counter)   # per DLC
PER = {}
SIL = collections.defaultdict(collections.Counter)
detail = []; unres = []; noxb = []
for rel in files:
    if rel not in PCD: continue
    P = PCD[rel]
    cands = xbox_raws(ALIAS.get(rel, rel))
    own = {s.id for s in P if s.type == 6}
    # stub di silenzio (indipendente dall'Xbox)
    silset = {s.id for s in P if s.type == 6 and is_silence(s.data)}
    nsil = len(silset)
    best = None
    for pk, xr in cands:
        try: X = DW.read(xr, 'be').sections
        except Exception as e: print('ERR XB', rel, pk, e); continue
        pr = pairs(X, P)
        sc = sum(1 for k, x, p in pr if x.id == p.id and len(x.data) == len(p.data))
        if best is None or sc > best[0]: best = (sc, pk, X, pr)
    dlc = DLC_OF[best[1]] if best else 'senza_xbox'
    c = collections.Counter()
    SIL[dlc]['onde'] += len(own); SIL[dlc]['silenzio'] += nsil
    if nsil: SIL[dlc]['file_con_silenzio'] += 1
    c['onde_sez'] = len(own); c['onde_silenzio'] = nsil
    # scansione solo-PC (tutti i DTP, valori senza filtro): riferimenti irrisolti
    for s in P:
        if s.type != 7 or not s.reloc: continue
        d = bytes(s.data)
        try: lv, kind = wave_leaves(d, R.parse(bytes(s.reloc), 'le'), 'le', max_id=None)
        except Exception: continue
        for tg in lv:
            v = struct.unpack_from('<I', d, tg)[0]
            c['pc_foglie'] += 1
            if v in NULLS: c['pc_null'] += 1
            elif v in own:
                c['pc_own'] += 1
                if v in silset: c['pc_own_silenzio'] += 1
            elif v in BASE_PC_WAVES: c['pc_base'] += 1
            elif v in ALL_WAVES: c['pc_altro_drm_dlc'] += 1
            else: c['pc_irrisolti'] += 1; unres.append('%s DTP %d +0x%x [%s] id %d' % (rel, s.id, tg, kind, v))
    if best:
        sc, pk, X, pr = best
        c['xbox_' + pk] = 1
        dtps = set()
        wavemap = {x.id: p.id for k, x, p in pr if x.type == 6 and p.type == 6}
        for k, x, p in pr:
            if x.type != 7 or not x.reloc: continue
            xd = bytes(x.data)
            try: xrel = R.parse(bytes(x.reloc), 'be'); lv, kind = wave_leaves(xd, xrel, 'be')
            except Exception as e: c['err_parse'] += 1; continue
            if not lv: continue
            if x.id != p.id and x.id in BASE.get(7, {}):
                c['dtp_base_rinumerati_saltati'] += 1; c['foglie_saltate_rinumerati'] += len(lv); continue
            pd = bytes(p.data)
            if len(pd) != len(xd) or not p.reloc or dict(R.parse(bytes(p.reloc), 'le').internal) != dict(xrel.internal):
                c['dtp_layout_diverso'] += 1; c['foglie_saltate_layout'] += len(lv); continue
            c['dtp_con_foglie'] += 1
            for tg in lv:
                c['foglie'] += 1
                if kind == 'embedded': c['foglie_incorporate'] += 1
                xw, pw = xd[tg:tg + 4], pd[tg:tg + 4]
                xv = struct.unpack('>I', xw)[0]; pv = struct.unpack('<I', pw)[0]
                want = xv if xv in NULLS else wavemap.get(xv, ids(6, xv))
                found = pv in NULLS or pv in own or pv in BASE_PC_WAVES
                if pv == want:
                    k0 = 'ok' if found else 'ok_muta'
                else:
                    if xv in NULLS: form = 'altro'
                    elif pv == ids(7, xv) and ids(7, xv) != xv: form = 'dtp_id'
                    elif pv == xv: form = 'non_mappato'
                    elif pv == bswap(xv): form = 'bswap'
                    elif pv == u16p(xv): form = 'u16pair'
                    else: form = 'altro'
                    k0 = 'sbagliata:' + form
                    c['p0_sbagliate'] += 1
                    sub = 'muta' if not found else ('onda_propria_sbagliata' if pv in own else 'id_base_fuori_DRM')
                    c['p0_sbagliate_' + sub] += 1; c['p0_sbagliate_' + kind] += 1; dtps.add(p.id)
                    if pv in own and pv in silset: c['p0_sbagliate_su_onda_silenzio'] += 1
                    if kind == 'embedded': c['p0_sbagliate_incorporate'] += 1
                c['p0:' + k0] += 1
                xw4, pw4 = xd[tg + 4:tg + 8], pd[tg + 4:tg + 8]
                ww4 = bytes(xw4[i] for i in PERMS['u8u8u16'])
                if pw4 == ww4: k4 = 'ok'
                else:
                    fs4 = [n for n, pm in PERMS.items() if bytes(xw4[i] for i in pm) == pw4]
                    k4 = 'sbagliata:' + ('+'.join(fs4) if fs4 else 'altro')
                    c['p4_sbagliate'] += 1
                c['p4:' + k4] += 1
                if k0 != 'ok' or k4 != 'ok':
                    detail.append('%s %s DTP %d->%d +0x%x [%s] +0 xb %d pc %d atteso %d %s | +4 xb %s pc %s %s' % (
                        dlc, rel, x.id, p.id, tg, kind, xv, pv, want, k0, xw4.hex(), pw4.hex(), k4))
    if best: c['dtp_con_sbagliate'] = len(dtps)
    else: noxb.append(rel)
    PER[rel] = (dlc, c)
    for kk, v in c.items(): TOT[dlc][kk] += v
    TOT[dlc]['file'] += 1

print('# waveid_scan su %s (%d DRM)' % (BL, len(files)))
print('# regola: +0 = wavemap/ids(6,x), 0/-1 invariati; +4 = u8u8u16; muta = id PC non onda del DRM ne\' onda base PC')
for dlc in sorted(TOT):
    t = TOT[dlc]
    print('\n== %s: %s' % (dlc, dict(sorted(t.items()))))
print('\n== stub di silenzio (sezioni tipo 6):', {k: dict(v) for k, v in SIL.items()})
print('\n== file con parole sbagliate (+0 sbagliate, +4 sbagliate, ok_muta, irrisolti solo-PC):')
rows = sorted(PER.items(), key=lambda kv: -(kv[1][1]['p0_sbagliate'] + kv[1][1]['p4_sbagliate']))
for rel, (dlc, c) in rows:
    if c['p0_sbagliate'] or c['p4_sbagliate'] or c['p0:ok_muta'] or c['pc_irrisolti']:
        print('%-8s %-45s p0 %4d (muta %d, id base fuori DRM %d, onda propria sbagliata %d; root0 %d incorp %d; DTP %d) p4 %4d ok_muta %d irris_PC %d foglie %d onde %d silenzio %d' % (
            dlc, rel, c['p0_sbagliate'], c['p0_sbagliate_muta'], c['p0_sbagliate_id_base_fuori_DRM'], c['p0_sbagliate_onda_propria_sbagliata'],
            c['p0_sbagliate_root0'], c['p0_sbagliate_embedded'], c['dtp_con_sbagliate'], c['p4_sbagliate'],
            c['p0:ok_muta'], c['pc_irrisolti'], c['foglie'], c['onde_sez'], c['onde_silenzio']))
print('\n== file con onde-silenzio:')
for rel, (dlc, c) in sorted(PER.items(), key=lambda kv: -kv[1][1]['onde_silenzio']):
    if c['onde_silenzio']: print('%-8s %-45s %d/%d' % (dlc, rel, c['onde_silenzio'], c['onde_sez']))
print('\n== DRM senza originale Xbox (%d):' % len(noxb), noxb)
print('\n== riferimenti irrisolti scansione solo-PC (%d):' % len(unres))
for l in unres: print(l)
print('\n== dettaglio parole non ok (%d):' % len(detail))
for l in detail: print(l)
