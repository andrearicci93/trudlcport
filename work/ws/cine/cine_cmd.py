"""Convertitore Xbox->PC delle LISTE COMANDI dei DRM cine (DTP con record {u16 tipo, u16 fotogramma}, ...).

Regole ricavate dalle coppie base Xbox/PC (dtp_rules.py, cmd16.py), verificate con validate():
  formato A (es. DLC 22643, 22604): record dall'offset 0
      lunghezza 12 + 4*(tipo>>12): {tipo,fot} s16 | uid s32 | {u16 a, u8, u8} | {msg,par} s16 | estra (0x2x: s16 o id DTP se msg 0x32; 0x3x: s32)
      altri (0x14,0x18,0x20,0x24,0x28) -> 20 B: come sopra + parola 4 s16, oppure s32 (id DTP) se msg == 50 o tipo 0x2405
  formato B (es. DLC 23766, base 7197): {u32 id DTP} + record da 16 B {tipo,fot} s16 | uid s32 | {msg,par} s16 | w s16;
      record 0x40xx: 16 B come sopra + puntatore + 2 float (s32) = 28 B; terminatore {ffff,0000} s16; poi testo (raw).
Gli id (uid, id DTP) sono scritti con id_map(kind, valore) se dato, altrimenti invariati (i DLC tengono i propri id).
"""
import struct

def _s32(w): return w[::-1]
def _s16(w): return w[1::-1] + w[3:1:-1]

def fmt_of(d):
    if len(d) >= 8 and d[0] >> 4 in (1, 2, 3) and d[0] & 3 == 0 and d[1] in (1, 2, 5): return 'A'
    if len(d) >= 8 and struct.unpack_from('>I', d, 0)[0] < 0x100000 and d[4] >> 4 in (1, 2, 3, 4) and d[5] in (1, 2, 5): return 'B'
    return None

def convert(d, id_map=None, ptrs=()):
    """d: dati Xbox (BE). Ritorna (bytes PC, mappa offset->classe). Solleva ValueError se la struttura non torna."""
    idm = id_map or (lambda kind, v: v)
    out = bytearray(d); cl = {}
    def put(o, c, kind=None):
        w = d[o:o + 4]
        if c == 'id':
            v = struct.unpack_from('>I', d, o)[0]; struct.pack_into('<I', out, o, idm(kind, v)); cl[o] = 'id'; return
        out[o:o + 4] = _s32(w) if c == 's32' else _s16(w) if c == 's16' else (w[1::-1] + w[2:4]) if c == 's16b2' else w; cl[o] = c
    f = fmt_of(d)
    if f is None: raise ValueError('formato non riconosciuto')
    o = 0; term = False
    if f == 'B': put(0, 'id', 'dtp'); o = 4
    while o + 4 <= len(d):
        t = struct.unpack_from('>H', d, o)[0]
        if t == 0xffff:                                    # terminatore {ffff,0000}; dopo (formato B) testo raw
            put(o, 's16'); o += 4; term = True; break
        cls_ = d[o] >> 4
        if d[o] & 3 or cls_ not in (1, 2, 3, 4): raise ValueError('tipo %#06x sconosciuto a %#x' % (t, o))
        n = (12 if f == 'A' else 8) + 4 * cls_
        if o + n > len(d): raise ValueError('record %#06x oltre la fine a %#x' % (t, o))
        put(o, 's16'); put(o + 4, 'id', 'uid'); put(o + 8, 's16b2' if f == 'A' else 's16')
        if f == 'A':
            put(o + 12, 's16')
            msg = struct.unpack_from('>H', d, o + 12)[0]
            if cls_ == 2: put(o + 16, 'id', 'dtp') if msg == 0x32 else put(o + 16, 's16')
            for k in range(16 if cls_ == 2 else 16, n, 4):
                if cls_ >= 3: put(o + k, 's32')
        else:
            if cls_ == 2: put(o + 12, 's16')
            elif cls_ == 4:
                if o + 12 not in ptrs: raise ValueError('record 0x4x senza puntatore a %#x' % (o + 12))
                cl[o + 12] = 'ptr'; put(o + 16, 's32'); put(o + 20, 's32')
            else:
                for k in range(12, n, 4): put(o + k, 's32')           # classe 1: nessuna; classe 3: parametri u32
        o += n
    if f == 'B' and not term: raise ValueError('formato B senza terminatore ffff0000')
    if f == 'A' and not term and o != len(d): raise ValueError('formato A non chiude')
    for k in range(o - o % 4, len(d), 4): cl.setdefault(k, 'raw')
    return bytes(out), cl


def validate():
    """Sulle coppie base: ogni parola non-id deve coincidere con il PC; per gli id si usa la mappa del PC stesso."""
    import sys, os, collections
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import cinepairs
    sys.path.insert(0, cinepairs.T)
    import drm_reloc as R
    tot = collections.Counter(); bad = []
    seen = set()
    for n, X, P in cinepairs.load():
        for x, p in zip([s for s in X if s['type'] == 7], [s for s in P if s['type'] == 7]):
            d = x['data']
            if fmt_of(d) is None or x['size'] != p['size'] or d in seen: continue
            seen.add(d)
            r = R.parse(x['reloc'], 'be'); ptrs = {a for a, b in r.internal}
            try:
                o, cl = convert(d, None, ptrs)
            except ValueError as e:
                tot['struttura_ko'] += 1; bad.append((n, x['id'], str(e))); continue
            q = p['data']; nw = 0
            for k in range(0, len(d) - 3, 4):
                c = cl.get(k)
                if c in ('id', 'ptr'): continue
                tot['parole'] += 1
                if o[k:k + 4] != q[k:k + 4]:
                    nw += 1; tot['sbagliate'] += 1
                    if len(bad) < 20: bad.append((n, x['id'], hex(k), c, d[k:k + 4].hex(), o[k:k + 4].hex(), q[k:k + 4].hex()))
            tot['dtp'] += 1; tot['dtp_esatti'] += (nw == 0)
    print(dict(tot))
    for b in bad[:20]: print('  ', b)

if __name__ == '__main__':
    validate()
