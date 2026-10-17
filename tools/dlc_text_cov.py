"""DLC menu text coverage helper (agent dlc_images): load locals tables of every source/language.
usage: tools/venv/bin/python -I tools/dlc_text_cov.py show SRC LANGIDX id[,id|a-b]..."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import locals as L
B = '/path/to/trudlcport/'
SPECS = L.SPECS
LANGNAME = {0xfffff7e1: 'en?', 0xfffff7e2: 'l1', 0xfffff7e4: 'l3', 0xfffff7e8: 'l2', 0xfffff7f0: 'l4', 0xffffffe0: 'l5'}
_cache = {}
def table(src, spec):
    """-> (lang, [bytes|None]) ; PC: offset 0 -> None (missing id)."""
    k = (src, spec)
    if k not in _cache:
        path, e, pre = L.SRC[src]
        from archive import Archive
        from names import crc
        a = Archive(path, e); recs = [r for r in a.find(crc(pre + '\\local\\locals.bin')) if r['spec'] == spec]
        b = a.read(recs[0]) if recs else None
        if b is None: _cache[k] = None
        else:
            lang, st, offs = L.parse(b, e)
            _cache[k] = (lang, [None if (i == 0 or o == 0) else s for i, (s, o) in enumerate(zip(st, offs))])
    return _cache[k]
def merged_table(spec):
    """work/generic/locals/mods/local/locals.bin_NNN"""
    suffix = (spec & 0x1f) if spec != 0xffffffe0 else 32
    p = B + 'work/generic/locals/mods/local/locals.bin_%03d' % suffix
    b = open(p, 'rb').read(); lang, st, offs = L.parse(b, 'le')
    return lang, [None if (i == 0 or o == 0) else s for i, (s, o) in enumerate(zip(st, offs))]

# ---- script member widget text ids (init block +0x5c) ----
import struct, pickle
import menu_dlc_probe as P
import drm_reloc as R

def members(C, v, sid, nm='generalbank.drm'):
    """-> list of (index, userType, initBlockOffset, u32 at +0x5c, init block bytes[0:0x80])"""
    e = P.SRC[v][1]; E = '>' if e == 'be' else '<'
    s = next((q for q in P.secs(C, v, nm) if q['type'] == 8 and q['id'] == sid and q['data']), None)
    if s is None: return []
    d = s['data']; rel = R.parse(s['reloc'], e); it = dict(rel.internal)
    if 0x2c not in it: return []
    t = it[0x2c]; n = struct.unpack_from(E + 'I', d, t - 4)[0]
    out = []
    for k in range(n):
        a = t + 20 * k
        ut = struct.unpack_from(E + 'H', d, a + 4)[0]
        ip = it.get(a + 16)
        if ip is not None and ip in it:
            b = it[ip]
            if b + 0x60 <= len(d): out.append((k, ut, b, struct.unpack_from(E + 'I', d, b + 0x5c)[0], d[b:b + 0x80]))
    return out
