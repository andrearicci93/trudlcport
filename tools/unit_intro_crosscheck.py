"""Cross-check placed objects (intros) of a BASE-GAME unit between the Xbox 360 original and the PC release, read-only.

Question type: "is this placed object on PC original design, or does it differ from the Xbox base game?" (2026-11-16,
a loose carryable pole in a Croft Manor unit). For every given unit and every game archive copy it lists the intros
whose object name matches --grep, with the PC intro id beside the Xbox one, and searches every section of the unit
DRMs for the given intro ids (does any other intro's data block or a script hold the id?).

Reads (writes only with --save): the unit DRM from each archive of tools/locals.py that has it - PC: pcpatch, pcbig; Xbox: tu, xbase,
xbase2 - so a copy that only the patch / title update changed is visible. Layout (tools/unit_ids.py,
work/endb270_0811/unit_dtp.py): unit DTP = target of Level (section 0) +0x74, intro count +0x0c, Intro* +0x10,
0x90-byte records: +0x00 rotation vec4, +0x10 position vec4, +0x40 scale, +0x50 u16 object id (per-platform object
list: work/generic/lists/pc_objectlist.txt / xbox_objectlist.txt), +0x58 u32 intro unique id (numbered per platform;
Xbox -> PC map in work/generic/unit_idmaps.json space 'intro'), +0x78 intro data pointer (internal relocation; size =
distance to the next relocation target in the DTP, as unit_dtp.py), +0x7c word.

Usage (from the repository root):
  ../bin/pyt -t 900 tools/unit_intro_crosscheck.py UNIT [UNIT ...] [--grep REGEX] [--ref PCID[,PCID]]
                    [--scan UNIT[,UNIT]] [--words N] [--u16-all] [--at SPEC[,SPEC]] [--save DIR]
    --grep   object name regex (default: everything)
    --ref    PC intro ids to search for; their Xbox ids come from the id map (both are searched on both platforms,
             as aligned u32 and as aligned u16 words, u16 not in textures / meshes unless --u16-all; every hit is
             printed with its owner and the surrounding words); --scan adds units that are only searched, not listed
    --words  intro data words printed per intro (default 16)
    --at     UNIT:SECTION_INDEX:OFFSET:LENGTH[,...] (hex offset / length): the words there on every copy (section
             indices of a base pair line up; 'R' = relocated pointer) - is a hit on one side the same field on the other?
    --save   DIR: also write each decoded unit DRM as DIR/<unit>_<source>.drm (for tools/drm_words_at.py; the only
             write, keep DIR outside the repository - game data)
Exit code: 0 = read, 2 = usage error.
"""
import sys, os, re, struct, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import locals as LC
import drm, drm_reloc as R
from archive import Archive
from names import crc

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
LISTS = os.path.join(ROOT, 'work', 'generic', 'lists')
IDMAP = os.path.join(ROOT, 'work', 'generic', 'unit_idmaps.json')
SIDES = {'pc': ['pcpatch', 'pcbig'], 'xbox': ['tu', 'xbase', 'xbase2']}


def opt(argv, name, default):
    if name in argv:
        i = argv.index(name)
        v = argv[i + 1]
        del argv[i:i + 2]
        return v
    return default


def objnames(side):
    d = {}
    for line in open(os.path.join(LISTS, side + '_objectlist.txt'), encoding='utf8', errors='ignore'):
        p = line.strip().split(',', 1)
        if len(p) == 2 and p[0].isdigit():
            d[int(p[0])] = p[1]
    return d


_arch = {}


def copies(side, unit):
    """[(source, raw DRM bytes)] of every archive of the side that holds the unit"""
    out = []
    for src in SIDES[side]:
        path, e, pre = LC.SRC[src]
        if not os.path.exists(path):
            continue
        A = _arch.setdefault(src, Archive(path, e))
        recs = A.find(crc(pre + '\\' + unit + '.drm'))
        if recs:
            out.append((src, drm.cdrm_decode(A.read(recs[0]), e)))
    return out


def parse(raw, e):
    """(sections, unit DTP index, internal pointer map of the DTP, intro list)"""
    S = drm.sections_with_data(raw, e)[1]
    tgt = [si for si, so, do in R.parse(S[0]['reloc'], e).external if so == 0x74]
    di = tgt[0]
    u = S[di]
    ptr = dict(R.parse(u['reloc'], e).internal)
    E = '>' if e == 'be' else '<'
    d = u['data']
    n = struct.unpack_from(E + 'I', d, 0xc)[0]
    a = ptr[0x10]
    tg = sorted(set(ptr.values()))
    intros = []
    for k in range(n):
        o = a + 0x90 * k
        dp = ptr.get(o + 0x78)
        dsz = (min([t for t in tg if t > dp] + [len(d)]) - dp) if dp is not None else 0
        intros.append(dict(k=k, o=o, rot=struct.unpack_from(E + '4f', d, o), pos=struct.unpack_from(E + '3f', d, o + 0x10),
                           scale=struct.unpack_from(E + '3f', d, o + 0x40), obj=struct.unpack_from(E + 'H', d, o + 0x50)[0],
                           uid=struct.unpack_from(E + 'I', d, o + 0x58)[0], raw78=struct.unpack_from(E + 'I', d, o + 0x78)[0],
                           dp=dp, dsz=dsz, w7c=struct.unpack_from(E + 'I', d, o + 0x7c)[0]))
    return S, di, ptr, intros


def owner(intros, di, si, off, L):
    """where a hit at (section, offset) lies: own intro record / an intro data block / a unit DTP table (tools/unit_ids.py
    level_info: 0xb0 'rec' records, 0x40 node records) / elsewhere"""
    if si != di:
        return ''
    for it in intros:
        if it['o'] <= off < it['o'] + 0x90:
            return 'intro record k=%d uid %d +0x%x' % (it['k'], it['uid'], off - it['o'])
        if it['dp'] is not None and it['dp'] <= off < it['dp'] + it['dsz']:
            return 'intro DATA of k=%d uid %d +0x%x' % (it['k'], it['uid'], off - it['dp'])
    for key, size in (('recs', 0xb0), ('nodes', 0x40), ('dportals', 0x40)):
        for k, (s2, o) in enumerate(L.get(key, []) if L else []):
            if s2 == si and o <= off < o + size:
                return 'unit DTP %s record %d +0x%x' % (key, k, off - o)
    return 'unit DTP, outside intro records / data / known tables'


def find_refs(S, di, intros, e, vals, u16_all=False):
    import unit_ids as U
    E = '>' if e == 'be' else '<'
    L = U.level_info(S, e)
    hits = []
    for si, s in enumerate(S):
        d = s['data']
        if d is None:
            continue
        if not u16_all and s['type'] in (5, 12):    # textures / meshes: u16 noise only, u32 still searched
            for v in vals:
                b32 = struct.pack(E + 'I', v)
                hits += [(v, 'u32', si, s['type'], s['id'], o) for o in range(0, len(d) - 3, 4) if d[o:o + 4] == b32]
            continue
        for v in vals:
            b32 = struct.pack(E + 'I', v)
            for o in range(0, len(d) - 3, 4):
                if d[o:o + 4] == b32:
                    hits.append((v, 'u32', si, s['type'], s['id'], o))
            if v < 0x10000:
                b16 = struct.pack(E + 'H', v)
                for o in range(0, len(d) - 1, 2):
                    if d[o:o + 2] == b16 and not (o % 4 == 0 and d[o:o + 4] == b32) and \
                            not (o % 4 == 2 and d[o - 2:o + 2] == b32):
                        hits.append((v, 'u16', si, s['type'], s['id'], o))
    out = []
    for v, w, si, t, sid, o in hits:
        d = S[si]['data']
        a, b = max(0, (o & ~3) - 8), min(len(d) & ~3, (o & ~3) + 12)
        ctx = ' '.join('%08x' % x for x in struct.unpack_from(E + '%dI' % ((b - a) // 4), d, a))
        out.append((v, w, si, t, sid, o, owner(intros, di, si, o, L), 'size 0x%x ctx@0x%x: %s' % (len(d), a, ctx)))
    return out


def main(argv):
    argv = list(argv)
    rx = opt(argv, '--grep', '.')
    refs = [int(x) for x in opt(argv, '--ref', '').split(',') if x]
    scan = [x.lower() for x in opt(argv, '--scan', '').split(',') if x]
    nwords = int(opt(argv, '--words', '16'))
    at = [x for x in opt(argv, '--at', '').split(',') if x]
    save = opt(argv, '--save', None)
    u16_all = '--u16-all' in argv
    if u16_all:
        argv.remove('--u16-all')
    if not argv:
        print(__doc__)
        return 2
    names = {'pc': objnames('pc'), 'xbox': objnames('xbox')}
    x2p = {int(k): v for k, v in json.load(open(IDMAP))['intro'].items()}
    p2x = {}
    for k, v in x2p.items():
        p2x.setdefault(v, k)
    refvals = {'pc': refs, 'xbox': [p2x[r] for r in refs if r in p2x]}
    if refs:
        print('ref ids PC %s -> Xbox %s (unit_idmaps.json)' % (refs, refvals['xbox']))
    units = [u.lower() for u in argv]
    for unit in units + [u for u in scan if u not in units]:
        listed = unit in units
        print('\n######## %s%s' % (unit, '' if listed else ' (ref search only)'))
        for side in ('xbox', 'pc'):
            e = 'be' if side == 'xbox' else 'le'
            E = '>' if e == 'be' else '<'
            cps = copies(side, unit)
            if not cps:
                print('== %s: not found in %s' % (side, '/'.join(SIDES[side])))
            for src, raw in cps:
                if save:
                    os.makedirs(save, exist_ok=True)
                    open(os.path.join(save, '%s_%s.drm' % (unit, src)), 'wb').write(raw)
                S, di, ptr, intros = parse(raw, e)
                d = S[di]['data']
                lo = struct.unpack_from(E + '3f', S[0]['data'], 0x80)
                print('== %s [%s] md5 %s: %d sections, unit DTP section %d id %d, %d intros, Level+0x80 (%.1f %.1f %.1f)'
                      ' (live position = intro position - this, ENGINE.md 4.3)' % (
                          side, src, hashlib.md5(raw).hexdigest()[:12], len(S), di, S[di]['id'], len(intros), *lo))
                if listed:
                    for it in intros:
                        nm = names[side].get(it['obj'], '?')
                        if not re.search(rx, nm, re.I):
                            continue
                        pcid = x2p.get(it['uid'], '?') if side == 'xbox' else it['uid']
                        print('   k=%3d uid %5d (PC id %s) obj %4d %-24s pos (%.1f %.1f %.1f) rot (%.4f %.4f %.4f %.4f) '
                              'scale (%.2f %.2f %.2f) +0x78 %s +0x7c %08x' % (
                                  it['k'], it['uid'], pcid, it['obj'], nm, it['pos'][0], it['pos'][1], it['pos'][2],
                                  it['rot'][0], it['rot'][1], it['rot'][2], it['rot'][3],
                                  it['scale'][0], it['scale'][1], it['scale'][2],
                                  ('data@0x%x size 0x%x' % (it['dp'], it['dsz'])) if it['dp'] is not None
                                  else 'no data (raw %08x)' % it['raw78'], it['w7c']))
                        if it['dp'] is not None and nwords:
                            n = min(nwords, it['dsz'] // 4)
                            w = struct.unpack_from(E + '%dI' % n, d, it['dp'])
                            rel = ['R' if (it['dp'] + 4 * j) in ptr else '' for j in range(n)]
                            print('        data words: %s' % ' '.join('%08x%s' % (a, r) for a, r in zip(w, rel)))
                for spec in at:
                    au, asi, aoff, aln = spec.split(':')
                    if au.lower() != unit:
                        continue
                    asi, aoff, aln = int(asi), int(aoff, 16), int(aln, 16)
                    s = S[asi]
                    sp = dict(R.parse(s['reloc'], e).internal)
                    n = max(0, min(aln, len(s['data']) - aoff) // 4)
                    w = struct.unpack_from(E + '%dI' % n, s['data'], aoff) if n else ()
                    print('   at section %d (type %d id %d size 0x%x) +0x%x: %s' % (
                        asi, s['type'], s['id'], len(s['data']), aoff,
                        ' '.join('%08x%s' % (x, 'R' if aoff + 4 * j in sp else '') for j, x in enumerate(w))))
                if refvals[side]:
                    for v, w, si, t, sid, o, where, ctx in find_refs(S, di, intros, e, refvals[side], u16_all):
                        print('   ref %d as %s: section %d (type %d id %d) +0x%x %s | %s' % (v, w, si, t, sid, o, where, ctx))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
