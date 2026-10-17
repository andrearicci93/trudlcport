"""Recover file names for unnamed hashes in the DLC packs (pack1/2/10/11) by dictionary hashing.

Hash = CRC-32/BZIP2 (poly 0x04C11DB7 MSB-first, init/xorout 0xffffffff) of the lower-case path (names.crc); a table-driven
version with prefix-state caching is used here (names.crc is bit-serial and slow).
Candidates: identifier strings found in all DLC files (DRM section data, raw .mul/.raw/other payloads), base filelist
basenames, DLC unit/object list names; combined with templates learned from the Xbox filelist (directories x extensions,
'<unit>_map', streamgroups '<unit>_<group>', music '<dir>\\<file>', image '<name>_preview' ...).
Output: work/generic/dlc_names.txt  (hash, pack, size, kind, name) for every DLC record, names resolved or '?'.
Usage: python3 -I tools/dlc_names.py
"""
import sys, os, re, json, struct, collections, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from archive import Archive
from names import load, L

TAB = []
for i in range(256):
    c = i << 24
    for _ in range(8): c = ((c << 1) ^ 0x4C11DB7) & 0xffffffff if c & 0x80000000 else (c << 1) & 0xffffffff
    TAB.append(c)

def upd(h, s):
    for ch in s.encode('latin1'):
        h = ((h << 8) & 0xffffffff) ^ TAB[(h >> 24) ^ ch]
    return h

import zlib
REV8 = bytes(int('{:08b}'.format(i)[::-1], 2) for i in range(256))
def rev32(v): return int('{:032b}'.format(v)[::-1], 2)
def fcrc(s, h0=None):
    """CRC-32/BZIP2 = bit-reversed zlib CRC-32 of bit-reversed bytes (C speed)"""
    return rev32(zlib.crc32(s.lower().encode('latin1').translate(REV8)))
assert fcrc('pc-w\\g_pda.drm') == (~upd(0xffffffff, 'pc-w\\g_pda.drm') & 0xffffffff)

C = '/path/to/Xenia-SteveRepack/Content/534307EC/00000002/'
PACKS = {'pack10': C + '9CA70CF0EDA43654D158C2E37470D301DFA850E753/pack10.000', 'pack11': C + '600A12643FCDAC84003E6E0DBD0A1A8F7DAE9DD153/pack11.000',
         'pack1': C + 'E5AFB2B959A72C52120D73678AED11BD8752686753/pack1.000', 'pack2': C + '9FDDD06617D1016DE468ACF53AC663E8BA2AD41853/pack2.000'}
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'generic')

def kind(b):
    if b[:4] == b'CDRM' or b[:4] == b'\0\0\0\x13': return 'drm'
    if b[:4] in (b'FSB4', b'FSB3'): return 'fsb'
    return b[:4].hex()

def main():
    xn = load(L + 'Tomb Raider Underworld (Xenon).txt')
    pcn = load(L + 'Tomb Raider Underworld (PC).txt')
    known = dict(xn)
    for f in ('dlc_names_recovered.txt',):
        p = os.path.join(W, f)
        if os.path.exists(p):
            for l in open(p):
                l = l.split()
                if len(l) == 2 and l[0].startswith('0x'): known[int(l[0], 16)] = l[1]
    recs = []; strings = set()
    from drm import cdrm_decode
    for pk, path in PACKS.items():
        A = Archive(path, 'be')
        for r in A.idx:
            b = A.read(r)
            k = kind(b)
            recs.append((r['hash'], pk, r['spec'], len(b), k))
            if k != 'drm': continue
            from drm import sections_with_data
            for sec in sections_with_data(cdrm_decode(b, 'be'), 'be')[1]:
                if sec['type'] not in (0, 2, 7, 8, 11, 13): continue
                for m in re.findall(rb'[A-Za-z0-9_\\/\.\-]{3,80}', sec['data']):
                    m = m.decode('latin1').lower()
                    if re.search('[a-z]{2}', m): strings.add(m)
    unk = {h for h, *_ in recs if h not in known}
    sys.stdout.flush(); print('records', len(recs), 'unknown hashes', len(unk), 'strings', len(strings))
    # name stems
    stems = set()
    for s in strings:
        s = s.replace('/', '\\').strip('\\.')
        stems.add(s)
        base = s.split('\\')[-1]
        stems.add(base); stems.add(base.rsplit('.', 1)[0])
    for n in itertools.chain(xn.values(), pcn.values()):
        b = n.split('\\')[-1].rsplit('.', 1)[0].lower(); stems.add(b)
    for f in ('dlc_pack11_unitlist.txt', 'dlc_pack10_unitlist.txt', 'dlc_pack11_objectlist.txt'):
        t = open(os.path.join(W, 'lists', f), 'rb').read().decode('latin1').split('\r\n')[1:]
        for l in t:
            if l: stems.add(l.split(',', 1)[-1].split('\\')[-1].lower())
    # directory templates from the Xbox filelist (dir, ext) pairs
    dirs = collections.Counter()
    for n in xn.values():
        n = n.lower()
        d, _, f = n.rpartition('\\'); e = f.rsplit('.', 1)[-1] if '.' in f else ''
        dirs[d, e] += 1
    tmpl = [(d, e) for (d, e), c in dirs.items()]
    # extra dirs: music subdirs named after units, dlc variants
    units = [s for s in stems if s.startswith('dlc')]
    for u in units:
        for e in ('mus', 'sam', 'mul'):
            tmpl.append(('xenon-w\\music\\' + u, e))
    found = {}
    pre_state = {}
    def try_name(full):
        h = fcrc(full)
        if h in unk and h not in found: found[h] = full
    cand = [s for s in stems if 2 < len(s) < 90]
    print('stems', len(cand), 'templates', len(tmpl))
    # compare in the bit-reversed domain: zlib.crc32(rev bytes) == rev32(target)
    unk_r = {rev32(h): h for h in unk}
    for d, e in tmpl:
        pre = ((d + '\\') if d else '').encode('latin1').translate(REV8)
        st0 = zlib.crc32(pre)
        suf = ('.' + e) if e else ''
        sufb = suf.encode('latin1').translate(REV8)
        for s in cand:
            if suf and s.endswith(suf): s = s[:-len(suf)]
            v = zlib.crc32(sufb, zlib.crc32(s.encode('latin1').translate(REV8), st0))
            h = unk_r.get(v)
            if h is not None and h not in found: found[h] = (d + '\\' if d else '') + s + suf
    # composed: streamgroups unit_group, unit_map, previews
    for u in units:
        for s in cand:
            for full in ('xenon-w\\streamgroups\\%s_%s.drm' % (u, s), 'xenon-w\\%s_%s.drm' % (u, s)):
                try_name(full)
    print('found', len(found))
    known.update(found)
    out = os.path.join(W, 'dlc_names.txt')
    st = collections.Counter()
    with open(out, 'w') as f:
        for h, pk, spec, size, k in sorted(recs, key=lambda r: (r[1], known.get(r[0], '~'))):
            nm = known.get(h, '?')
            st[pk, 'named' if nm != '?' else 'unnamed', k if k in ('drm', 'fsb') else 'other'] += 1
            f.write('0x%08x %-7s %08x %9d %-8s %s\n' % (h, pk, spec, size, k, nm))
    for k, v in sorted(st.items()): print(k, v)
    print('wrote', out)

if __name__ == '__main__':
    main()
