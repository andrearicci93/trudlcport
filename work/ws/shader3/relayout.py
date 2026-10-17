# Layout ShaderLib (tipo 9) verificato: entry = u32 junk, u32 size (intera entry, incluso junk+size), u64 hash, payload = raw[16:size].
# payload = bytecode (fino al token FFFF incluso) + trailer. Offset slot relativi a section+4.
import struct
def read_entries(data, e='<'):
    tb, ds = struct.unpack_from(e + 'II', data, 4)
    slots = list(struct.unpack_from(e + '%dI' % (tb // 4), data, 12))
    ents = {}
    for o in sorted(set(s for s in slots if s != 0xffffffff)):
        raw = data[4 + o:4 + o + struct.unpack_from(e + 'I', data, 4 + o + 4)[0]]
        ents[o] = raw
    return data[:4], tb, slots, ents
def bytecode_len(payload, e='<'):
    n = len(payload) // 4
    t = struct.unpack_from(e + '%dI' % n, payload, 0)
    i = 1
    while i < n:
        tok = t[i]; op = tok & 0xFFFF
        if op == 0xFFFF: return (i + 1) * 4
        if op == 0xFFFE: i += 1 + ((tok >> 16) & 0x7FFF); continue
        i += 1 + ((tok >> 24) & 0xF)
    raise ValueError('no end token')
def relayout(data, replace=None, e='<'):
    """replace: {offset_vecchio: nuovo_payload}. Ordine e trailer originali; offset ricalcolati."""
    kp, tb, slots, ents = read_entries(data, e)
    base = 8 + tb
    newoff = {}; body = bytearray()
    for o in sorted(ents):
        raw = ents[o]
        junk = raw[0:4]; h = raw[8:16]; pl = raw[16:]
        if replace and o in replace: pl = replace[o]
        newoff[o] = base + len(body)
        body += junk + struct.pack(e + 'I', 16 + len(pl)) + h + pl
    table = struct.pack(e + '%dI' % len(slots), *[s if s == 0xffffffff else newoff[s] for s in slots])
    out = kp + struct.pack(e + 'II', tb, 0) + table + bytes(body)
    return out[:8] + struct.pack(e + 'I', len(out) - 4) + out[12:]   # ds = lunghezza da section+4

def relayout_contig(data, patch=None, e='<'):
    """Per libreria con campo size non affidabile: entry = [offset, offset_successivo) (ultima fino a fine sezione).
    patch: {offset_vecchio: nuovo_payload_da_16} sostituisce il payload (dal byte 16 dell'entry), junk/size/hash restano."""
    tb, ds = struct.unpack_from(e + 'II', data, 4)
    slots = list(struct.unpack_from(e + '%dI' % (tb // 4), data, 12))
    offs = sorted(set(s for s in slots if s != 0xffffffff))
    ends = {o: (offs[k + 1] if k + 1 < len(offs) else len(data) - 4) for k, o in enumerate(offs)}
    out_body = bytearray(); newoff = {}
    for o in offs:
        ent = data[4 + o:4 + ends[o]]
        if patch and o in patch: ent = ent[:16] + patch[o]
        newoff[o] = len(out_body) + 8 + tb       # relativo a section+4
        out_body += ent
    table = struct.pack(e + '%dI' % len(slots), *[s if s == 0xffffffff else newoff[s] for s in slots])
    head = data[:4] + struct.pack(e + 'II', tb, 0) + table + bytes(out_body)
    return head[:8] + struct.pack(e + 'I', len(head) - 4) + head[12:]
