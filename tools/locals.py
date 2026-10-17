"""locals.bin (localised string table) reader/writer + DLC merge for PC.

Format (Yura LocaleFile; verified by byte-exact round trip below): platform endian
  u32 language, u32 n, u32 offset[n] (absolute file offsets), then NUL-terminated UTF-8 strings.
One file per language; bigfile entries share the name hash and differ by specMask (language bits):
  0xffffffe0 / 0xfffff7e1 / 0xfffff7e2 / 0xfffff7e4 / 0xfffff7e8 / 0xfffff7f0.
Strings are referenced by INDEX from game data, so the merge keeps PC indices and only fills indices that PC lacks.

Usage: python3 -I tools/locals.py survey      (compare all versions)
       python3 -I tools/locals.py build [out]  -> <out>/mods/local/locals.bin_<NNN> (ModLoader per-language name:
            '%s_%03d' % (path, specMask & ~0x80000000); NNN = 001/002/004/008/016 from the spec low bits, 032 for 0xffffffe0 = GUESS)
            + <out>/locmap_xbox_to_pc.json (Xbox TU string index -> PC string id, for the data converters)
"""
import sys, os, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from archive import Archive
from names import crc

B = '/path/to/'
C = B + 'Xenia-SteveRepack/Content/534307EC/00000002/'
SRC = {'xbase': (B + 'TombRaiderUnderworld_Patched/layer1.000', 'be', 'xenon-w'), 'xbase2': (B + 'TombRaiderUnderworld_Patched/layer2.000', 'be', 'xenon-w'),
       'tu': (B + 'TombRaiderUnderworld_Patched/TitleUpdate.000', 'be', 'xenon-w'),
       'pcbig': (B + 'tru-port/pc/bigfile.000', 'le', 'pc-w'), 'pcpatch': (B + 'tru-port/pc/patch.000', 'le', 'pc-w'),
       'pack10': (C + '9CA70CF0EDA43654D158C2E37470D301DFA850E753/pack10.000', 'be', 'xenon-w'),
       'pack11': (C + '600A12643FCDAC84003E6E0DBD0A1A8F7DAE9DD153/pack11.000', 'be', 'xenon-w'),
       'pack1': (C + 'E5AFB2B959A72C52120D73678AED11BD8752686753/pack1.000', 'be', 'xenon-w'),
       'pack2': (C + '9FDDD06617D1016DE468ACF53AC663E8BA2AD41853/pack2.000', 'be', 'xenon-w')}

def parse(b, endian):
    e = '>' if endian == 'be' else '<'
    lang, n = struct.unpack_from(e + 'II', b, 0)
    offs = struct.unpack_from(e + '%dI' % n, b, 8)
    out = []
    for o in offs:
        z = b.index(b'\0', o)
        out.append(b[o:z])
    return lang, out, offs

def write(lang, strings, endian, dedup=False):
    e = '>' if endian == 'be' else '<'
    n = len(strings)
    hdr = 8 + 4 * n
    body = bytearray(); offs = []; seen = {}
    for s in strings:
        if dedup and s in seen: offs.append(seen[s]); continue
        offs.append(hdr + len(body)); seen[s] = offs[-1]
        body += s + b'\0'
    return struct.pack(e + 'II', lang, n) + struct.pack(e + '%dI' % n, *offs) + bytes(body)

def files(src):
    path, e, pre = SRC[src]
    a = Archive(path, e)
    return {r['spec']: a.read(r) for r in a.find(crc(pre + '\\local\\locals.bin'))}, e

def survey():
    V = {}
    for s in SRC:
        f, e = files(s)
        if not f: continue
        V[s] = {}
        for spec, b in sorted(f.items()):
            lang, st, offs = parse(b, e)
            exact = write(lang, st, e) == b
            dexact = write(lang, st, e, dedup=True) == b
            V[s][spec] = (lang, st)
            print('%-8s spec %08x lang %3d strings %5d bytes %7d  roundtrip %s dedup-roundtrip %s' % (s, spec, lang, len(st), len(b), exact, dexact))
    return V

def compare(V):
    for spec in sorted(V['pcpatch']):
        pc = V['pcpatch'][spec][1]; pb = V['pcbig'][spec][1] if spec in V.get('pcbig', {}) else None
        xb = V['xbase'][spec][1]; tu = V['tu'][spec][1]
        d = lambda a, b: sum(1 for i in range(min(len(a), len(b))) if a[i] != b[i])
        line = 'spec %08x: n pcbig %s pcpatch %d xbase %d tu %d' % (spec, len(pb) if pb else '-', len(pc), len(xb), len(tu))
        line += ' | diff(xbase,pcbig) %s diff(tu,pcpatch) %d diff(xbase,tu) %d' % (d(xb, pb) if pb else '-', d(tu, pc), d(xb, tu))
        for p in ('pack10', 'pack11', 'pack1'):
            if spec in V.get(p, {}):
                line += ' | %s n %d diff(tu) %d' % (p, len(V[p][spec][1]), d(V[p][spec][1], tu))
        print(line)

SPECS = (0xfffff7e1, 0xfffff7e2, 0xfffff7e4, 0xfffff7e8, 0xfffff7f0, 0xffffffe0)

def build_map(V):
    """Xbox TU string index -> PC string id.
    1. base indices: unique-string equality Xbox base table vs PC patch table, voted over the 6 languages (>=4 votes)
    2. indices inside a consistent span of mapped neighbours (m[b]-m[a]==b-a) are interpolated
    3. everything else (TU/DLC-new indices >= 1284 and base indices without a PC counterpart) is APPENDED after the
       PC table (new ids 5136+), in Xbox index order. Index 0 is the null entry (0 -> 0)."""
    votes = collections.defaultdict(collections.Counter)
    for spec in SPECS:
        X = V['xbase'][spec][1]; P = V['pcpatch'][spec][1]
        offs = parse(files_cache['pcpatch'][spec], 'le')[2]
        idx = collections.defaultdict(list)
        for i, s in enumerate(P):
            if offs[i] != 0: idx[s].append(i)
        for i, s in enumerate(X):
            c = idx.get(s)
            if s and c and len(c) == 1: votes[i][c[0]] += 1
    m = {0: 0}
    for x, c in votes.items():
        (p, n), = c.most_common(1)
        if n >= 4: m[x] = p
    inv = collections.Counter(m.values()); m = {k: v for k, v in m.items() if inv[v] == 1}
    nbase = len(V['xbase'][SPECS[0]][1]); ntu = len(V['tu'][SPECS[0]][1])
    ks = sorted(m); interp = 0
    for a, b in zip(ks, ks[1:]):
        if b - a > 1 and m[b] - m[a] == b - a:
            for x in range(a + 1, b): m[x] = m[a] + x - a; interp += 1
    npc = len(V['pcpatch'][SPECS[0]][1]); nxt = npc; appended = []
    for x in range(1, ntu):
        if x not in m: m[x] = nxt; nxt += 1; appended.append(x)
    return m, dict(matched=len(votes), mapped_by_string=len(ks), interpolated=interp, appended=len(appended),
                   appended_base=sum(1 for x in appended if x < nbase), appended_dlc=sum(1 for x in appended if x >= nbase), pc_n=npc, tu_n=ntu)

def merged(V, spec, m):
    """PC patch table + TU strings: appended ids get the TU text; a mapped base id whose PC text equals the Xbox
    BASE text (placeholder like 'DLC TEST MISSION 2' / 'Extra Costume 1') but changed in the TU gets the TU text."""
    pc = list(V['pcpatch'][spec][1]); lang = V['pcpatch'][spec][0]
    X = V['xbase'][spec][1]; T = V['tu'][spec][1]
    n = max(m.values()) + 1
    pc += [b''] * (n - len(pc))
    st = collections.Counter()
    for x, p in m.items():
        if x == 0: continue
        if p >= len(V['pcpatch'][spec][1]): pc[p] = T[x]; st['appended'] += 1
        elif x < len(X) and T[x] != X[x] and pc[p] == X[x]: pc[p] = T[x]; st['placeholder_replaced'] += 1
        elif x < len(X) and T[x] != X[x]: st['tu_changed_but_pc_differs_kept_pc'] += 1
    return lang, pc, st

def write_pc(lang, strings, offs_pc):
    """PC layout: index 0 and PC 'missing' ids point at offset 0 (the header) like the shipped PC file."""
    n = len(strings); hdr = 8 + 4 * n
    body = bytearray(); offs = []; seen = {}
    for i, s in enumerate(strings):
        if i == 0 or (i < len(offs_pc) and offs_pc[i] == 0): offs.append(0); continue
        if s in seen: offs.append(seen[s]); continue
        offs.append(hdr + len(body)); seen[s] = offs[-1]; body += s + b'\0'
    return struct.pack('<II', lang, n) + struct.pack('<%dI' % n, *offs) + bytes(body)

files_cache = {}

if __name__ == '__main__':
    import json
    for k in SRC:
        f, e = files(k)
        if f: files_cache[k] = f
    V = survey()
    compare(V)
    if sys.argv[1:2] == ['build']:
        out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(B, 'tru-port/work/generic/locals')
        m, info = build_map(V)
        print('map', info)
        os.makedirs(out, exist_ok=True)
        json.dump({'rule': build_map.__doc__, 'info': info, 'map': {str(k): v for k, v in sorted(m.items())}},
                  open(os.path.join(out, 'locmap_xbox_to_pc.json'), 'w'))
        d = os.path.join(out, 'mods', 'local'); os.makedirs(d, exist_ok=True)
        for spec in SPECS:
            lang, strings, st = merged(V, spec, m)
            offs_pc = parse(files_cache['pcpatch'][spec], 'le')[2]
            b = write_pc(lang, strings, offs_pc)
            back = parse(b, 'le')[1]
            ok = all(back[i] == strings[i] for i in range(len(strings)) if not (i == 0 or (i < len(offs_pc) and offs_pc[i] == 0)))
            # unchanged PC entries must survive
            pcs = V['pcpatch'][spec][1]
            keep = sum(1 for i in range(len(pcs)) if back[i] == pcs[i])
            suffix = (spec & 0x1f) if spec != 0xffffffe0 else 32
            fn = os.path.join(d, 'locals.bin_%03d' % suffix)
            open(fn, 'wb').write(b)
            print('wrote', fn, 'spec %08x lang %d n %d' % (spec, lang, len(strings)), dict(st), 'readback ok', ok, 'PC entries unchanged %d/%d' % (keep, len(pcs)))
