"""faults_scan.py - (19/11/2026) SOLA LETTURA. Riscrittura nostra delle famiglie di difetti del convertitore del fork di
Lukas (fork tools/converter_faults_fix.py, finding 44: idword, statevm, chartid, fxnode, objevent, animlist), applicate
a un nostro albero baseline (DRM PC LE) contro l'originale Xbox (pack11 / pack10 / pack1 / pack2). Nessun codice del
fork importato o eseguito: logica riletta e riscritta.

Sezioni abbinate PER POSIZIONE (difflib su (tipo, dimensione), come il fork); coppia con id PC != id Xbox =
"base-mapped" (DTP base rinumerato preso dal gioco base): differenze contate a parte (kept), non come errori.

Famiglie:
  idword   liste eventi oggetto (DTP che l'oggetto tipo 11 nomina a +4): record kind 1 con sub u16 0x32 a payload+0,
           parola payload 1 (rec+12) = UN u32 (id sezione) -> PC = Xbox byte-reversed. In piu' (stessa regola, nel fork
           sta in animlist): le liste eventi anim (u32 0 in testa) con record kind 1 sub 0x32.
  statevm  DTP con codice VM (reloc interno a +0 -> +4, blocchi ai target di +4/+8/+0xc): ogni parola di codice (non
           puntatore/id) = u32 -> PC = Xbox reversed.
  fxnode   nodi effetto {u32 tipo<=13, ptr dati, u32 self id = id DTP, u32 0}: header u32 (self id = id PC del DTP),
           nodi tipo 1: parola dati = u32 id sezione (ok, oppure "rinumerato" se valore PC e' un id di sezione).
  chartid  state chart (parole 3..6 = 10000,12000,4000,6000): voci attivita' {u16 id, u16 tipo, valore} di tipo 3/5 =
           u32 id sezione, valore atteso = id PC del DTP allineato con l'id Xbox (mappa difflib, blocchi 'equal').
           La tabella base x_lara/pc_lara (che nel fork ha priorita') NON e' disponibile qui (Xbox base non su questo PC).
  objevent PARZIALE: solo parole strutturali (parola 0 dei record u16+u16, terminatore u16, self id dopo il
           terminatore = u32 dell'id PC della lista). Le parole payload dipendono dalla tabella appresa da x_lara/pc_lara:
           qui solo la distribuzione di come il PC le ha scritte (nessun verdetto).
  animlist PARZIALE: parola 0 dei record {u16 h, s16 frame} come due u16, terminatore u16 (+ sub 0x32 in idword).
uso: python -I -B faults_scan.py BASELINE FAMIGLIA[,FAMIGLIA..] [--max N]
log: inv/faults_<famiglia>_<BASELINE>.log (una per famiglia)
"""
import sys, os, struct, collections, difflib
sys.path.insert(0, '/path/to/trudlcport/tools')
import drm_write as DW, drm_reloc as R
from archive import Archive
from dlc_names import PACKS, fcrc

BS = chr(92)
INV = os.path.dirname(os.path.abspath(__file__))
FAMS = ('idword', 'statevm', 'fxnode', 'chartid', 'objevent', 'animlist')
PACK_ORDER = ('pack11', 'pack10', 'pack1', 'pack2')
DLC_OF = {'pack11': 'DLC2', 'pack10': 'DLC1', 'pack1': 'costumi', 'pack2': 'costumi'}
NOTE_SID = {20212: 'DTP 20212 doppel (zona B235/B272/B273)'}

_A = {}
def arch(p):
    if p not in _A: _A[p] = Archive(PACKS[p], 'be')
    return _A[p]

def xbox(rel, PD=None):
    """(raw Xbox, pack, altri pack con lo stesso nome). Con PD e nome in piu' pack: sceglie il pack la cui lista
    sezioni (tipo, dimensione) si abbina meglio al DRM PC (piu' sezioni accoppiate per posizione)."""
    h = fcrc('xenon-w' + BS + rel.replace('/', BS))
    got = []
    for p in PACK_ORDER:
        rs = [r for r in arch(p).idx if r['hash'] == h]
        if rs: got.append((p, rs[0]))
    if not got: return None, None, []
    if PD is not None and len(got) > 1:
        sc = []
        for p, r in got:
            raw = arch(p).read(r)
            sc.append((len(pairs_by_position(DW.read(raw, 'be'), PD)), p, raw))
        sc.sort(key=lambda t: -t[0])
        return sc[0][2], sc[0][1], ['%s(%d vs %d abbinate)' % (p, n, sc[0][0]) for n, p, _ in sc[1:]]
    p, r = got[0]
    return arch(p).read(r), p, [q for q, _ in got[1:]]

def how(x4, p4, want):
    if p4 == want: return 'ok'
    if p4 == x4: return 'raw'
    if p4 == bytes(x4[1::-1] + x4[3:1:-1]): return 'u16'
    if p4 == x4[::-1]: return 'u32'
    return 'other'

def pairs_by_position(XD, PD):
    a = [(s.type, len(s.data)) for s in XD.sections]; b = [(s.type, len(s.data)) for s in PD.sections]
    out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == 'equal' or (tag == 'replace' and i2 - i1 == j2 - j1 and [t for t, _ in a[i1:i2]] == [t for t, _ in b[j1:j2]]):
            out += [(j1 + k, XD.sections[i1 + k], PD.sections[j1 + k]) for k in range(j2 - j1)]
    return out

def id_map(XD, PD):
    a = [(s.type, len(s.data)) for s in XD.sections]; b = [(s.type, len(s.data)) for s in PD.sections]
    m = {}
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag != 'equal': continue
        for k in range(i2 - i1):
            m.setdefault(XD.sections[i1 + k].id, set()).add((XD.sections[i1 + k].type, PD.sections[j1 + k].id))
    return m

def slots(s, e):
    r = R.parse(bytes(s.reloc), e)
    return set(r.pointer_offsets()) | set(r.id_offsets())

# ------------------------------------------------------------ strutture
def objects(D, e):
    f = '>' if e == 'be' else '<'
    dtp = {s.id: s for s in D.sections if s.type == 7}
    out = []
    for s in D.sections:
        if s.type != 11: continue
        lst = None
        if len(s.data) >= 8 and R.parse(bytes(s.reloc), e).id_offsets().get(4) == 7:
            lst = dtp.get(struct.unpack_from(f + 'I', s.data, 4)[0])
        out.append((s, lst))
    return out

def ow_walk(d, e):
    """lista eventi oggetto: record {u16 h, .., payload (h>>12)*4}, fine u16 0xffff"""
    f = '>' if e == 'be' else '<'
    a = 0; recs = []
    while a + 2 <= len(d) and len(recs) < 100000:
        h = struct.unpack_from(f + 'H', d, a)[0]
        if h == 0xffff: return recs, a
        sz = (h >> 12) * 4 + 8
        if a + sz > len(d): return recs, None
        recs.append((a, h, sz)); a += sz
    return recs, None

def an_walk(d, e):
    """lista eventi anim: u32 0, record {u16 h, s16 frame, ..}, 1..8 parole payload, fine u16 0xffff"""
    if len(d) < 8 or d[:4] != b'\0\0\0\0': return None
    a = 4; out = []
    while a + 4 <= len(d):
        h, fr = struct.unpack_from(e + 'Hh', d, a)
        if h == 0xffff: return (out, a) if out else None
        sz = (h >> 12) * 4 + 8
        if fr < 0 or not 1 <= (h >> 12) <= 8 or a + sz > len(d): return None
        out.append((a, h, fr, sz)); a += sz
    return None

def code_blocks(s, e):
    it = dict(R.parse(bytes(s.reloc), e).internal)
    if it.get(0) != 4: return []
    return [it[o] for o in (4, 8, 0xc) if o in it]

def code_words(s, e):
    b = code_blocks(s, e)
    if not b: return {}
    E = '>' if e == 'be' else '<'
    sk = slots(s, e); out = {}
    for st in b:
        end = min([x for x in b if x > st] + [len(s.data)])
        for p in range(st, end - 3, 4):
            if p not in sk: out[p] = struct.unpack_from(E + 'I', s.data, p)[0]
    return out

def fx_nodes(s, e):
    E = '>' if e == 'be' else '<'
    if s.type != 7 or len(s.data) < 16: return []
    it = dict(R.parse(bytes(s.reloc), e).internal)
    out = []
    for o in range(0, len(s.data) - 15, 4):
        t, _, sid, z = struct.unpack_from(E + 'IIII', s.data, o)
        if t <= 13 and (o + 4) in it and sid == s.id and z == 0: out.append((o, t, it[o + 4]))
    return out

HDR = struct.pack('>4I', 10000, 12000, 4000, 6000)
def is_chart_be(d): return len(d) >= 0x1c and d[0xc:0x1c] == HDR

def chart_records(s, e):
    f = '>' if e == 'be' else '<'
    d = bytes(s.data); it = dict(R.parse(bytes(s.reloc), e).internal); out = []
    for o in sorted(it):
        r = o - 0x14
        if r < 0 or r % 8 or r + 0x28 > len(d): continue
        if struct.unpack_from(f + 'I', d, r + 0x24)[0]: continue
        if not all((r + k) in it for k in (0x14, 0x18, 0x1c, 0x20)): continue
        if any((r + k) in it for k in (0, 4, 8, 0xc, 0x10, 0x24)): continue
        hdr = struct.unpack_from(f + '10H', d, r)
        p = [it[r + k] for k in (0x14, 0x18, 0x1c, 0x20)]
        if p[0] + 8 * hdr[5] > len(d) or p[1] + 2 * hdr[6] > len(d) or p[2] + 2 * hdr[7] > len(d) or p[3] + 2 * hdr[8] > len(d): continue
        out.append((r, hdr, p[0]))
    return out

# ------------------------------------------------------------ risultato
class Res:
    def __init__(self):
        self.c = collections.Counter(); self.files = collections.Counter(); self.dlc = collections.Counter()
        self.rows = []; self.kept = []; self.odd = []
    def wrong(self, rel, dlc, s, xid, o, x4, p4, want, note):
        self.c['wrong'] += 1; self.files[rel] += 1; self.dlc[dlc] += 1
        self.rows.append('%s [%s] 7:%d (Xbox %d) +0x%x xbox %s pc %s atteso %s %s%s' % (
            rel, dlc, s.id, xid, o, bytes(x4).hex(), bytes(p4).hex(), bytes(want).hex(), note,
            ('  <' + NOTE_SID[s.id] + '>') if s.id in NOTE_SID else ''))
    def keep(self, rel, dlc, s, xid, o, x4, p4, want, note):
        self.c['base-mapped diversi (kept)'] += 1
        self.kept.append('%s [%s] 7:%d (Xbox %d) +0x%x xbox %s pc %s regola %s %s' % (rel, dlc, s.id, xid, o, bytes(x4).hex(), bytes(p4).hex(), bytes(want).hex(), note))
    def strange(self, rel, dlc, text):
        self.c['unexpected'] += 1; self.odd.append('%s [%s] %s' % (rel, dlc, text))

def word(R_, rel, dlc, s, xid, mapped, o, x4, p4, want, note, allow=('raw', 'u16')):
    """classifica una parola: ok / errata (raw|u16 = byte order sbagliato) / altro"""
    x4, p4, want = bytes(x4), bytes(p4), bytes(want)
    if p4 == want: R_.c['ok'] += 1; return
    k = how(x4, p4, want)
    if mapped: R_.keep(rel, dlc, s, xid, o, x4, p4, want, note + ' ' + k); return
    if k in allow: R_.wrong(rel, dlc, s, xid, o, x4, p4, want, note + ' ' + k)
    else: R_.strange(rel, dlc, '7:%d +0x%x xbox %s pc %s atteso %s %s (%s)' % (s.id, o, x4.hex(), p4.hex(), want.hex(), note, k))

# ------------------------------------------------------------ famiglie
def f_idword(R_, rel, dlc, XD, PD, PP):
    ids = {s.id for s in PD.sections}
    xo, po = objects(XD, 'be'), objects(PD, 'le')
    if len(xo) != len(po): R_.c['file con numero oggetti diverso (liste oggetto non confrontate)'] += 1
    else:
        for (xs, xl), (ps, pl) in zip(xo, po):
            if xl is None or pl is None: continue
            mapped = xl.id != pl.id
            rp, _ = ow_walk(pl.data, 'le'); rx, _ = ow_walk(xl.data, 'be')
            if len(xl.data) != len(pl.data) or len(rp) != len(rx) or any(a[:3] != b[:3] for a, b in zip(rp, rx)):
                R_.c['liste oggetto non uguali (non confrontate)'] += 1; continue
            R_.c['liste oggetto'] += 1
            ptr = set(R.parse(bytes(xl.reloc), 'be').pointer_offsets())
            for a, h, sz in rx:
                if h & 3 != 1 or sz < 16 or struct.unpack_from('>H', xl.data, a + 8)[0] != 0x32 or a + 12 in ptr: continue
                R_.c['record oggetto sub 0x32'] += 1
                x4 = xl.data[a + 12:a + 16]; xw = struct.unpack('>I', x4)[0]
                word(R_, rel, dlc, pl, xl.id, mapped, a + 12, x4, pl.data[a + 12:a + 16], x4[::-1],
                     'obj %d lista sub0x32 id %d%s' % (ps.id, xw, '' if xw in ids else ' (NON sezione)'))
    for k, x, p in PP:   # liste anim, stesso sub 0x32 (nel fork: animlist)
        if x.type != 7 or len(x.data) != len(p.data): continue
        w = an_walk(x.data, '>')
        if w is None: continue
        mapped = x.id != p.id
        for a, h, fr, sz in w[0]:
            if h & 3 != 1 or sz < 16 or struct.unpack_from('>H', x.data, a + 8)[0] != 0x32: continue
            if a + 12 in slots(x, 'be'): continue
            R_.c['record anim sub 0x32'] += 1
            x4 = x.data[a + 12:a + 16]; xw = struct.unpack('>I', x4)[0]
            word(R_, rel, dlc, p, x.id, mapped, a + 12, x4, p.data[a + 12:a + 16], x4[::-1],
                 'anim sub0x32 id %d%s' % (xw, '' if xw in ids else ' (NON sezione)'))

def f_statevm(R_, rel, dlc, XD, PD, PP):
    for k, x, p in PP:
        if x.type != 7: continue
        wx = code_words(x, 'be')
        if not wx: continue
        wp = code_words(p, 'le'); mapped = x.id != p.id
        if len(x.data) != len(p.data): R_.c['dimensione diversa (non confrontata)'] += 1; continue
        if set(wp) != set(wx): R_.strange(rel, dlc, '7:%d layout codice diverso (stessa dimensione)' % p.id); continue
        R_.c['sezioni'] += 1; R_.c['parole'] += len(wp)
        for o in sorted(wp):
            x4 = x.data[o:o + 4]
            word(R_, rel, dlc, p, x.id, mapped, o, x4, p.data[o:o + 4], x4[::-1], 'vm')

def f_fxnode(R_, rel, dlc, XD, PD, PP):
    ids = {s.id for s in PD.sections}
    for k, x, p in PP:
        if x.type != 7: continue
        nx = fx_nodes(x, 'be')
        if not nx: continue
        if len(x.data) != len(p.data): R_.c['dimensione diversa (non confrontata)'] += 1; continue
        mapped = x.id != p.id; R_.c['DTP con nodi'] += 1
        pin = dict(R.parse(bytes(p.reloc), 'le').internal)
        for o, t, dx in nx:
            if pin.get(o + 4) != dx:
                R_.strange(rel, dlc, '7:%d nodo +0x%x: puntatore PC +4 %s, Xbox -> +0x%x' % (p.id, o, pin.get(o + 4), dx)); continue
            for w, val in ((0, t), (8, p.id), (12, 0)):
                R_.c['parole header'] += 1
                x4 = x.data[o + w:o + w + 4]
                word(R_, rel, dlc, p, x.id, mapped, o + w, x4, p.data[o + w:o + w + 4], struct.pack('<I', val),
                     'nodo +0x%x %s' % (o, ('tipo', '', 'self id', 'zero')[w // 4]))
            if t != 1 or dx + 4 > len(p.data): continue
            R_.c['nodi tipo 1'] += 1
            x4 = x.data[dx:dx + 4]; p4 = p.data[dx:dx + 4]; xw = struct.unpack('>I', x4)[0]; pw = struct.unpack('<I', p4)[0]
            if pw == xw: R_.c['tipo1 ok'] += 1; continue
            k2 = how(x4, p4, x4[::-1])
            if k2 == 'other' and pw in ids: R_.c['tipo1 rinumerati (id PC valido)'] += 1; continue
            if k2 in ('raw', 'u16') and xw in ids:
                if mapped: R_.keep(rel, dlc, p, x.id, dx, x4, p4, x4[::-1], 'tipo1 id %d %s' % (xw, k2))
                else: R_.wrong(rel, dlc, p, x.id, dx, x4, p4, x4[::-1], 'nodo +0x%x tipo1 id %d %s' % (o, xw, k2))
                continue
            if mapped: R_.c['base-mapped diversi (kept)'] += 1; continue
            R_.strange(rel, dlc, '7:%d nodo +0x%x dati +0x%x: PC 0x%08x Xbox 0x%08x (%s, valore PC %s sezione)' % (
                p.id, o, dx, pw, xw, k2, 'e\'' if pw in ids else 'NON'))

def f_chartid(R_, rel, dlc, XD, PD, PP):
    M = None
    for k, x, p in PP:
        if x.type != 7 or not is_chart_be(bytes(x.data)): continue
        if len(x.data) != len(p.data): R_.c['chart dimensione diversa (non confrontati)'] += 1; continue
        rx, rp = chart_records(x, 'be'), chart_records(p, 'le')
        mapped = x.id != p.id
        if len(rx) != len(rp): R_.strange(rel, dlc, '7:%d record diversi (Xbox %d PC %d)' % (p.id, len(rx), len(rp))); continue
        R_.c['chart'] += 1
        if M is None: M = id_map(XD, PD)
        for (r, hx, lx), (_, hp, lp) in zip(rx, rp):
            for i in range(hx[5]):
                ex, ep = lx + 8 * i, lp + 8 * i
                eid, et = struct.unpack_from('>HH', x.data, ex)
                if et not in (3, 5): continue
                R_.c['voci tipo 3/5'] += 1
                x4 = x.data[ex + 4:ex + 8]; xv = struct.unpack('>I', x4)[0]; p4 = p.data[ep + 4:ep + 8]
                t7 = sorted({q for t, q in M.get(xv, set()) if t == 7})
                if len(t7) != 1:
                    pv = struct.unpack('<I', p4)[0]
                    R_.c['senza valore provato (serve tabella base)'] += 1
                    R_.odd.append('%s [%s] INFO 7:%d voce +0x%x id %d tipo %d Xbox 0x%x PC 0x%x (%s): nessun DTP allineato unico' % (
                        rel, dlc, p.id, ep, eid, et, xv, pv, how(x4, p4, x4[::-1])))
                    continue
                want = struct.pack('<I', t7[0])
                if p4 == want: R_.c['ok'] += 1; continue
                k2 = how(x4, p4, want)
                note = 'id %d tipo %d Xbox 0x%x -> %d (mappa DTP) PC 0x%x %s' % (eid, et, xv, t7[0], struct.unpack('<I', p4)[0], k2)
                if mapped: R_.keep(rel, dlc, p, x.id, ep + 4, x4, p4, want, note)
                else: R_.wrong(rel, dlc, p, x.id, ep + 4, x4, p4, want, note)

def conv16(x4): return bytes(x4[1::-1] + x4[3:1:-1])

def f_objevent(R_, rel, dlc, XD, PD, PP):
    xo, po = objects(XD, 'be'), objects(PD, 'le')
    if len(xo) != len(po): R_.c['file con numero oggetti diverso'] += 1; return
    for (xs, xl), (ps, pl) in zip(xo, po):
        if xl is None or pl is None: continue
        mapped = xl.id != pl.id
        rx, end = ow_walk(xl.data, 'be')
        if len(xl.data) != len(pl.data) or end is None: R_.c['liste non confrontate (dim. diversa / Xbox non cammina)'] += 1; continue
        R_.c['liste'] += 1; R_.c['record'] += len(rx)
        sk = slots(xl, 'be')
        for a, h, sz in rx:
            if a not in sk:
                x4 = xl.data[a:a + 4]
                word(R_, rel, dlc, pl, xl.id, mapped, a, x4, pl.data[a:a + 4], conv16(x4), 'obj %d rec hdr' % ps.id)
            for w in range(1, sz // 4):
                o = a + 4 * w
                if o in sk: continue
                if h & 3 == 1 and sz >= 16 and w == 3 and struct.unpack_from('>H', xl.data, a + 8)[0] == 0x32: continue  # idword
                x4 = bytes(xl.data[o:o + 4]); p4 = bytes(pl.data[o:o + 4])
                if x4 == x4[::-1] and conv16(x4) == x4: R_.c['payload invarianti'] += 1; continue
                R_.c['payload (non verificati) PC=%s' % how(x4, p4, b'')] += 1
        x4 = xl.data[end:end + 4]; p4 = pl.data[end:end + 4]
        want = conv16(x4)[:2] + bytes(p4[2:])
        word(R_, rel, dlc, pl, xl.id, mapped, end, x4, p4, want, 'obj %d terminatore' % ps.id)
        for o in range((end + 4 + 3) // 4 * 4, len(xl.data) // 4 * 4, 4):
            if o in sk or struct.unpack_from('>I', xl.data, o)[0] != xl.id: continue
            R_.c['self id'] += 1
            word(R_, rel, dlc, pl, xl.id, mapped, o, xl.data[o:o + 4], pl.data[o:o + 4], struct.pack('<I', pl.id), 'obj %d self id' % ps.id, allow=('raw', 'u16', 'u32', 'other'))

def f_animlist(R_, rel, dlc, XD, PD, PP):
    for k, x, p in PP:
        if x.type != 7 or len(x.data) != len(p.data): continue
        w = an_walk(x.data, '>')
        if w is None: continue
        mapped = x.id != p.id; R_.c['liste'] += 1
        sk = slots(x, 'be')
        st = [(a, x.data[a:a + 4], conv16(x.data[a:a + 4])) for a, h, fr, sz in w[0] if a not in sk]
        st.append((w[1], x.data[w[1]:w[1] + 4], conv16(x.data[w[1]:w[1] + 4])[:2] + bytes(p.data[w[1] + 2:w[1] + 4])))
        if mapped:
            if all(bytes(p.data[a:a + 4]) == wt for a, _, wt in st): R_.c['base-mapped con framing Xbox (controllate)'] += 1; mapped = False
            else: R_.c['base-mapped con altro framing (saltate)'] += 1; continue
        for a, x4, wt in st:
            word(R_, rel, dlc, p, x.id, mapped, a, x4, p.data[a:a + 4], wt, 'anim hdr/term')
        for a, h, fr, sz in w[0]:
            for q in range(1, sz // 4):
                o = a + 4 * q
                if o in sk: continue
                if h & 3 == 1 and sz >= 16 and q == 3 and struct.unpack_from('>H', x.data, a + 8)[0] == 0x32: continue
                x4 = bytes(x.data[o:o + 4]); p4 = bytes(p.data[o:o + 4])
                if x4 == x4[::-1] and conv16(x4) == x4: R_.c['payload invarianti'] += 1; continue
                R_.c['payload (non verificati) PC=%s' % how(x4, p4, b'')] += 1

FN = {f: globals()['f_' + f] for f in FAMS}

def main():
    base = sys.argv[1]; fams = sys.argv[2].split(',')
    mx = int(sys.argv[sys.argv.index('--max') + 1]) if '--max' in sys.argv else 400
    B = '/path/to/trudlcport/work/baseline/%s/mods/' % base
    res = {f: Res() for f in fams}
    nfile = collections.Counter(); multi = []; noxb = []
    for root, _, fs in os.walk(B):
        for f in sorted(fs):
            if not f.lower().endswith('.drm'): continue
            rel = os.path.relpath(os.path.join(root, f), B).replace(BS, '/')
            try: PD = DW.read(open(os.path.join(root, f), 'rb').read(), 'le')
            except Exception as e: print('ERR', rel, e); continue
            xr, pk, others = xbox(rel, PD)
            if xr is None: noxb.append(rel); continue
            if others: multi.append('%s: %s (+%s)' % (rel, pk, ','.join(others)))
            dlc = DLC_OF[pk]
            try: XD = DW.read(xr, 'be')
            except Exception as e: print('ERR', rel, e); continue
            nfile[dlc] += 1
            PP = pairs_by_position(XD, PD)
            for fm in fams:
                try: FN[fm](res[fm], rel, dlc, XD, PD, PP)
                except Exception as e: res[fm].strange(rel, dlc, 'ECCEZIONE %r' % e)
    for fm in fams:
        r = res[fm]
        L = ['famiglia %s su %s (file con originale Xbox: %s; senza: %d; nome in piu\' pack: %d)' % (
            fm, base, dict(nfile), len(noxb), len(multi))]
        L.append('conteggi: ' + ', '.join('%s %d' % kv for kv in sorted(r.c.items())))
        L.append('errate per DLC: %s' % dict(r.dlc))
        L.append('file peggiori: ' + ', '.join('%s %d' % kv for kv in r.files.most_common(15)))
        L.append('--- parole errate (%d, prime %d) ---' % (len(r.rows), mx)); L += r.rows[:mx]
        L.append('--- unexpected / info (%d, prime %d) ---' % (len(r.odd), mx)); L += r.odd[:mx]
        L.append('--- base-mapped diversi, non contati (%d, prime 60) ---' % len(r.kept)); L += r.kept[:60]
        L.append('--- nomi in piu\' pack (scelto il pack con piu\' sezioni abbinate) ---'); L += multi
        L.append('--- senza originale Xbox (%d) ---' % len(noxb)); L += noxb
        p = os.path.join(INV, 'faults_%s_%s.log' % (fm, base))
        open(p, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
        print('\n'.join(L[:4])); print('  -> %s' % p)

if __name__ == '__main__':
    main()
