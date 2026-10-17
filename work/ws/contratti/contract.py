"""Contratto materiale <-> shader: lettori indipendenti e controlli statici (16/10/2026, sessione 'contratti').

Contesto. Un materiale PC lega ogni texture a un registro sampler tramite il byte SLOT del suo record da 16 B
(u32 texId, u32 lodBias, u32 type, u8 flag, u8 SLOT, u16 filter). La lib PS in pos2 della tupla campiona quei registri.
Il contratto e' rotto se, per un registro campionato, la texture legata ha tipo diverso (2D/cubo) oppure -- caso piu' sottile,
invisibile al solo controllo dimensionale -- e' un'ALTRA texture di quella che l'originale Xbox legava allo stesso sampler.

Questo modulo non importa nulla del traduttore: solo lettori (DRM, materiale, texture, ShaderLib, token D3D9).
  entries(data, reloc, endian)        -> record texture del materiale
  tex_table(drm)                      -> {id: {'kind': '2d'|'cube', 'fmt', 'w', 'h'}} (header PCD9, flags 0x8000 = cubo)
  frame_lib(section_data)             -> variante per slot, con riconoscimento esplicito della convenzione di framing
  bytecode_samplers(bc)               -> ({reg: kind} dichiarati, {reg: kind} campionati da texld/texldl/texldd...)
  dimension_rows(drm_path)            -> righe del controllo dimensionale (tutte le lib PS della tupla, non solo pos2)
CLI: tools/venv/bin/python -I work/ws/contratti/contract.py dim TREE_MODS_DIR [--json out.json]
"""
import sys, os, struct, collections, glob, json
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'work/ws/shader4'))
from f3_common import sm3dis            # solo per bytecode_len (taglio al token END)
import drm_write, drm_reloc as R

SAMPLER_OPS = {66, 95, 93}               # texld/texldb/texldp (66), texldl (95), texldd (93)
KIND = {2: '2d', 3: 'cube', 4: 'vol'}


def entries(data, reloc, endian):
    """Record texture del materiale, nell'ordine dei reloc id-ref tipo 5. endian 'le'|'be'."""
    rel = R.parse(reloc, endian); E = '>' if endian == 'be' else '<'
    out = []
    for t, o in sorted(rel.idref + rel.idref_a, key=lambda x: x[1]):
        if t == 5:
            tid, bias, ty, fl, slot, filt = struct.unpack_from(E + 'IIIBBH', data, o)
            out.append(dict(off=o, tex=tid, bias=bias, type=ty, flag=fl, slot=slot, filter=filt))
    return out


def tex_table(drm):
    """{id: dict(kind, fmt, w, h)} delle sezioni texture PCD9 di un DRM letto con drm_write.read()."""
    t = {}
    for s in drm.sections:
        if s.type == 5 and len(s.data) >= 24 and s.data[:4] == b'PCD9':
            fl = struct.unpack_from('<H', s.data, 0x16)[0]
            t[s.id] = dict(kind='cube' if fl & 0x8000 else '2d', fmt=s.data[4:8].decode('latin1'),
                           w=struct.unpack_from('<H', s.data, 0x10)[0], h=struct.unpack_from('<H', s.data, 0x12)[0])
    return t


def _reg(tok):
    """(regtype, num) del token di registro D3D9: tipo = bit 28-30 + bit 11-12."""
    return ((tok >> 28) & 7) | ((tok >> 8) & 0x18), tok & 0x7FF


def bytecode_samplers(bc):
    """({reg: kind} dichiarati da dcl, {reg} campionati) di un PS D3D9 (SM2/SM3). Commenti (CTAB) saltati per lunghezza."""
    n = len(bc) // 4
    t = struct.unpack_from('<%dI' % n, bc, 0)
    decl, used = {}, set()
    i = 1
    while i < n:
        tok = t[i]; op = tok & 0xFFFF
        if op == 0xFFFE:
            i += 1 + ((tok >> 16) & 0x7FFF); continue
        if op == 0xFFFF: break
        ln = (tok >> 24) & 0xF
        if op == 0x1F and i + 2 < n:                                       # dcl_<type> sN
            rt, rn = _reg(t[i + 2])
            if rt == 10: decl[rn] = KIND.get((t[i + 1] >> 27) & 0xF, '?')
        elif op in SAMPLER_OPS:
            for j in range(i + 1, min(i + 1 + ln, n)):                       # l'operando sampler e' l'ultimo di tipo 10
                rt, rn = _reg(t[j])
                if rt == 10 and (t[j] & 0x80000000): used.add(rn)
        i += 1 + ln
    return decl, used


def frame_lib(d):
    """Lettura indipendente di una ShaderLib (sezione tipo 9, LE). Ritorna dict(kind, slots, entries, errors, convention).
    Convenzione osservata nei 497 ShaderLib di B83: dataSize = len(sezione)-4; low16(size) = lunghezza dell'INTERO record
    (16 B di header + bytecode); high16 = metadati non interpretati, CONSERVATI (ritornati in 'meta')."""
    errs = []
    kind = d[0]
    tb, ds = struct.unpack_from('<II', d, 4)
    slots = list(struct.unpack_from('<%dI' % (tb // 4), d, 12))
    if ds != len(d) - 4: errs.append('dataSize %d != len-4 %d' % (ds, len(d) - 4))
    offs = sorted(set(s for s in slots if s != 0xFFFFFFFF))
    ents = {}
    for k, o in enumerate(offs):
        a = 4 + o
        if a + 16 > len(d): errs.append('entry %d fuori sezione' % o); continue
        junk, size = struct.unpack_from('<II', d, a)
        total = size & 0xFFFF; meta = size >> 16
        nxt = 4 + offs[k + 1] if k + 1 < len(offs) else len(d)
        conv = 'record_total'
        end = a + total
        if end != nxt:
            conv = 'legacy_hash_blob'; end = a + 8 + total            # vecchia convenzione: size = hash + blob
            if end != nxt:
                errs.append('entry @%d: confine %d != prossima entry/fine %d (size=%#x)' % (o, a + total, nxt, size)); continue
        bc = d[a + 16:end]
        L = sm3dis.bytecode_len(bc)
        if L != len(bc) and not (len(bc) - L < 8 and conv == 'legacy_hash_blob'):
            errs.append('entry @%d: byte extra dopo END (%d)' % (o, len(bc) - L))
        ents[o] = dict(hash=bytes(d[a + 8:a + 16]), bc=bytes(bc[:L]), meta=meta, junk=junk, convention=conv, record_len=total)
    hs = [e['hash'] for e in ents.values()]
    if len(set(hs)) != len(hs): errs.append('hash8 duplicati nella lib')
    return dict(kind=kind, slots=slots, entries=ents, errors=errs,
                convention=sorted({e['convention'] for e in ents.values()}))


def lib_registers(d):
    """(kind lib, {reg: set(kind)}, {reg} campionati) su tutte le varianti di una lib PS."""
    f = frame_lib(d)
    decl = collections.defaultdict(set); used = set()
    if f['kind'] != 1: return f['kind'], {}, set()
    for e in f['entries'].values():
        dd, uu = bytecode_samplers(e['bc'])
        for r, k in dd.items(): decl[r].add(k)
        used |= uu
    return 1, dict(decl), used


def read_tree(mods_dir):
    """{rel: drm_write.Drm} per tutti i .drm sotto mods_dir."""
    out = {}
    for p in sorted(glob.glob(os.path.join(mods_dir, '**', '*.drm'), recursive=True)):
        try: out[os.path.relpath(p, mods_dir)] = drm_write.read(open(p, 'rb').read(), 'le')
        except Exception as ex:
            out[os.path.relpath(p, mods_dir)] = ex
    return out


def dimension_rows(rel, drm):
    """Controllo dimensionale su tutte le lib PS della tupla (pos0..3) e tutti i record con registro campionato.
    Riga: file, material, pos, lib, reg, tex, flag, type, actual, expected, status."""
    rows = []
    libs9 = {s.id: s for s in drm.sections if s.type == 9}
    tex = tex_table(drm)
    cache = {}
    for s in drm.sections:
        if s.type != 10: continue
        tup = struct.unpack_from('<4I', s.data, 0x28)
        ents = entries(s.data, s.reloc, 'le')
        byslot = collections.defaultdict(list)
        for e in ents: byslot[e['slot']].append(e)
        for pos, lid in enumerate(tup):
            if lid not in libs9: continue
            if lid not in cache: cache[lid] = lib_registers(libs9[lid].data)
            kind, decl, used = cache[lid]
            if kind != 1: continue
            for r in sorted(used):
                for e in byslot.get(r, []):
                    t = tex.get(e['tex'])
                    if t is None:
                        status = 'texture_non_nel_file'
                    elif decl.get(r) == {t['kind']}: status = 'ok'
                    else: status = 'MISMATCH'
                    rows.append(dict(file=rel, material=s.id, pos=pos, lib=lid, reg=r, tex=e['tex'], flag=e['flag'], type=e['type'],
                                     actual=t['kind'] if t else None, expected=sorted(decl.get(r, [])), status=status))
                if not byslot.get(r):
                    rows.append(dict(file=rel, material=s.id, pos=pos, lib=lid, reg=r, tex=None, flag=None, type=None, actual=None,
                                     expected=sorted(decl.get(r, [])), status='registro_campionato_senza_entry'))
    return rows


def summarize(rows):
    mism = [r for r in rows if r['status'] == 'MISMATCH']
    grp = collections.OrderedDict()
    for r in mism: grp.setdefault((r['material'], r['pos'], r['lib'], r['reg'], r['tex']), []).append(r['file'])
    return mism, grp


def main():
    if len(sys.argv) < 3 or sys.argv[1] != 'dim':
        sys.exit(__doc__)
    tree = read_tree(sys.argv[2])
    rows = []
    for rel, d in tree.items():
        if isinstance(d, Exception): print('ILLEGGIBILE', rel, d); continue
        rows += dimension_rows(rel, d)
    mism, grp = summarize(rows)
    c = collections.Counter(r['status'] for r in rows)
    print('DRM %d, righe %d, stati %s' % (len(tree), len(rows), dict(c)))
    print('MISMATCH: %d occorrenze, %d casi distinti (materiale, pos, lib, reg, tex), %d materiali' % (
        len(mism), len(grp), len({k[0] for k in grp})))
    for k, v in grp.items(): print('  mat %d pos %d lib %d s%d tex %s  (%d DRM)' % (*k, len(v)))
    if '--json' in sys.argv:
        json.dump(rows, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=0)
    return 1 if mism else 0


if __name__ == '__main__':
    sys.exit(main())
