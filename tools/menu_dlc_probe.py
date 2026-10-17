"""Probe for the Xbox 'DOWNLOADABLE CONTENT' main-menu entry vs PC (agent menu_dlc, 2026-10-12).

Loads generalbank.drm in 4 variants: xl = Xbox layers (retail), xt = Xbox TitleUpdate, pb = PC bigfile, pp = PC patch.000.
Usage: tools/venv/bin/python -I tools/menu_dlc_probe.py scripts [variant]      list Script sections (+native name)
       tools/venv/bin/python -I tools/menu_dlc_probe.py strings variant id     printable strings of one section
       tools/venv/bin/python -I tools/menu_dlc_probe.py find variant v1,v2..   find u16/u32 values (platform endian) in all sections
Results are cached in work/menu_dlc/gb_cache.pkl.
"""
import sys, os, struct, pickle, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from archive import Archive
from drm import cdrm_decode, sections_with_data
from names import crc
import drm_reloc as R
B = '/path/to/'
OUT = B + 'tru-port/work/menu_dlc/'
CACHE = OUT + 'gb_cache.pkl'
SRC = {'xl': ([B + 'TombRaiderUnderworld_Patched/layer1.000', B + 'TombRaiderUnderworld_Patched/layer2.000'], 'be', 'xenon-w'),
       'xt': ([B + 'TombRaiderUnderworld_Patched/TitleUpdate.000'], 'be', 'xenon-w'),
       'pb': ([B + 'tru-port/pc/bigfile.000'], 'le', 'pc-w'),
       'pp': ([B + 'tru-port/pc/patch.000'], 'le', 'pc-w')}

def load_drm(var, name):
    paths, e, pre = SRC[var]
    for p in paths:
        a = Archive(p, e)
        r = a.find(crc(pre + '\\' + name))
        if r: return sections_with_data(cdrm_decode(a.read(r[0]), e), e), e
    return None, e

def cache(names=('generalbank.drm',)):
    if os.path.exists(CACHE):
        C = pickle.load(open(CACHE, 'rb'))
    else:
        C = {}
    ch = False
    for nm in names:
        for v in SRC:
            if (v, nm) not in C:
                C[v, nm] = load_drm(v, nm); ch = True
    if ch:
        os.makedirs(OUT, exist_ok=True); pickle.dump(C, open(CACHE, 'wb'))
    return C

def secs(C, v, nm='generalbank.drm'):
    d = C[v, nm][0]
    return d[1] if d else []

def cstr(d, o):
    z = d.find(b'\0', o)
    return d[o:z].decode('latin1') if z >= 0 else None

def script_info(s, e):
    d = s['data']
    rel = R.parse(s['reloc'], e)
    it = dict(rel.internal)
    E = '>' if e == 'be' else '<'
    nat = cstr(d, it[0x10]) if 0x10 in it else None
    pkg = cstr(d, it[0x0c]) if 0x0c in it else None
    size = struct.unpack_from(E + 'H', d, 0x1c)[0]
    return pkg, nat, size

def main():
    cmd = sys.argv[1]
    C = cache()
    if cmd == 'scripts':
        vs = sys.argv[2:] or list(SRC)
        for v in vs:
            e = SRC[v][1]
            for i, s in enumerate(secs(C, v)):
                if s['type'] == 8 and s['data']:
                    pkg, nat, size = script_info(s, e)
                    strs = [m.group().decode() for m in re.finditer(rb'[ -~]{6,}', s['data'])][:3]
                    print(v, i, s['id'], s['size'], pkg, nat, hex(size), strs)
    elif cmd == 'strings':
        v, sid = sys.argv[2], int(sys.argv[3])
        for s in secs(C, v):
            if s['id'] == sid and s['data']:
                print('type', s['type'], 'size', s['size'])
                for m in re.finditer(rb'[ -~]{4,}', s['data']): print(hex(m.start()), m.group().decode())
    elif cmd == 'find':
        v = sys.argv[2]; vals = [int(x, 0) for x in sys.argv[3].split(',')]
        E = '>' if SRC[v][1] == 'be' else '<'
        for s in secs(C, v):
            d = s['data']
            if not d: continue
            for val in vals:
                for fmt, w in (('H', 2), ('I', 4)):
                    pat = struct.pack(E + fmt, val)
                    for m in re.finditer(re.escape(pat), d):
                        if m.start() % w == 0:
                            print(v, 'type', s['type'], 'id', s['id'], fmt, val, hex(m.start()))
    elif cmd == 'members':
        v, sid = sys.argv[2], int(sys.argv[3])
        members(C, v, sid)
    elif cmd == 'dis':
        v, sid = sys.argv[2], int(sys.argv[3])
        only = set(int(x) for x in sys.argv[4].split(',')) if len(sys.argv) > 4 else None
        dis(C, v, sid, only=only)


def func_index(C, v, sid, off, nm='generalbank.drm'):
    """offset inside script sid -> ('f', k) function index / ('p', k) prototype index / None"""
    import script_conv as SC
    e = SRC[v][1]
    for s in secs(C, v, nm):
        if s['type'] == 8 and s['id'] == sid and s['data']:
            W = SC.Walk(s['data'], R.parse(s['reloc'], e), e).run()
            for name, t, n, sz in W.arrays:
                if name in ('funcs', 'protos') and t <= off < t + n * sz and (off - t) % sz == 0:
                    return (name[0], (off - t) // sz)
            return ('?', off)
    return None

def members(C, v, sid, nm='generalbank.drm', out=sys.stdout):
    """member list: index, type tag, userType sym, instance offset, name sym, init block (+ first uitext string id)"""
    import script_conv as SC
    e = SRC[v][1]; E = '>' if e == 'be' else '<'
    S = secs(C, v, nm)
    s = next(q for q in S if q['type'] == 8 and q['id'] == sid and q['data'])
    d = s['data']; rel = R.parse(s['reloc'], e); it = dict(rel.internal)
    t = it[0x2c]; n = struct.unpack_from(E + 'I', d, t - 4)[0]
    for k in range(n):
        a = t + 20 * k
        tag = struct.unpack_from(E + 'I', d, a)[0]; ut = struct.unpack_from(E + 'H', d, a + 4)[0]
        off, sym = struct.unpack_from(E + 'HH', d, a + 12)
        ip = it.get(a + 16)
        txt = ''
        if ip is not None and ip in it:          # depth-0 pointer -> widget init block
            b = it[ip]
            if b + 0x60 <= len(d): txt = 'w+5c=%d' % struct.unpack_from(E + 'I', d, b + 0x5c)[0]
        print('%3d tag %04x ut %5d off 0x%04x sym %5d init %s %s' % (k, tag, ut, off, sym, hex(ip) if ip else '-', txt), file=out)

PUSHF = 0x02   # push float literal: 1 extra word (missing from script_conv.Walk.EXTRA)

def dis(C, v, sid, nm='generalbank.drm', out=sys.stdout, only=None):
    import script_conv as SC
    e = SRC[v][1]; E = '>' if e == 'be' else '<'
    S = secs(C, v, nm)
    s = next(q for q in S if q['type'] == 8 and q['id'] == sid and q['data'])
    d = s['data']; rel = R.parse(s['reloc'], e)
    W = SC.Walk(d, rel, e).run()
    it = dict(rel.internal)
    ext = {so: (S[si]['type'], S[si]['id'], do) for si, so, do in rel.external}
    ids = rel.id_offsets()
    pk, nat, size = script_info(s, e)
    print('script %s id %d size %d native %s/%s inst 0x%x super %s' % (v, sid, len(d), pk, nat, size, ext.get(0x18) or struct.unpack_from(E + 'I', d, 0x18)[0]), file=out)
    protos = {}
    for name, t, n, sz in W.arrays:
        if name == 'protos':
            for k in range(n):
                a = t + k * sz
                fl = d[a + 4:a + 8]
                vt = struct.unpack_from(E + 'H', d, a + 6)[0]
                sym = struct.unpack_from(E + 'HH', d, a + 8)
                pid = ext.get(a) or struct.unpack_from(E + 'I', d, a)[0]
                protos[a] = (k, vt, sym, pid)
    for name, t, n, sz in W.arrays:
        if name != 'funcs': continue
        for k in range(n):
            if only is not None and k not in only: continue
            a = t + k * sz
            pr = it.get(a) or ext.get(a)
            st = d[a + 5]
            pinfo = protos.get(pr) if isinstance(pr, int) else pr
            ct = it.get(a + 0x18)
            if ct is None: continue
            cn = struct.unpack_from(E + 'I', d, ct - 4)[0]
            print('\n== func %d @0x%x state %d proto %s code @0x%x n=%d' % (k, a, st, pinfo, ct, cn), file=out)
            j = 0
            while j < cn:
                o = ct + 4 * j
                w = struct.unpack_from(E + 'I', d, o)[0]
                op = w >> 24; arg = w & 0xffffff
                extra = SC.Walk.EXTRA.get(op, 1 if op == PUSHF else 0)
                ann = []
                for q in range(1, extra + 1):
                    ao = o + 4 * q
                    aw = struct.unpack_from(E + 'I', d, ao)[0]
                    if ao in it:
                        tt = it[ao]; txt = cstr(d, tt)
                        ann.append('->int 0x%x %r' % (tt, txt[:60] if txt and all(32 <= ord(c) < 127 for c in txt) and txt else None))
                    elif ao in ext:
                        ty, tid, do = ext[ao]
                        fi = func_index(C, v, tid, do, nm) if ty == 8 else None
                        ann.append('->ext (%d,%d)+0x%x %s' % (ty, tid, do, fi))
                    elif ao in ids:
                        ann.append('->id type%d %d' % (ids[ao], aw))
                    else:
                        ann.append('raw 0x%x' % aw)
                print('  %04x  %08x  op%02x %6d  %s' % (o, w, op, arg if arg < 0x800000 else arg - 0x1000000, ' | '.join(ann)), file=out)
                j += 1 + extra


if __name__ == '__main__':
    main()
