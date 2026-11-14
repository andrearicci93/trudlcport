r"""TruMenu 0.22.53 sonar load scope: what the game loads when the PDA sonar opens, and what the two owner switches
would add - (1) "Nachbar-Stockwerke nachladen" = one step further (the off-floor neighbours' neighbours, loaded
without recursion) and (2) "Alles Verbundene laden" = every portal-connected map unit (recursive, any floor).
Read only; the data come from work/sonar_1411b/sonar_floors.py (PC bigfile maps, DLC maps from the Xbox packs = the
header words the converter keeps; the installed DLC copies have the same masks / portals, finding 02249).

Usage (from trudlcport):
  ../bin/pyt work/menu53_1411/sonar/s53_counts.py starts UNIT [UNIT ...]     one table row per start unit
  ../bin/pyt work/menu53_1411/sonar/s53_counts.py level PREFIX [...]         every map unit with the prefix as start;
                                                                             the row of the worst start + components
  ../bin/pyt work/menu53_1411/sonar/s53_counts.py save                       reveal-entry save size of every map
Rule replayed (0x6e2e60, called from the load callback 0x6e4df0 when +0xb2 is set): stop when the unit's mask misses
the floor; else per portal neighbour: skip when loaded / loading / its known mask misses the floor, else request
(recursive). Floor = lowest bit of the start's mask (0x6df600 -> 0x6ddb00).
Faces = both meshes minus the faces with flag +0xc & 0x40 (never drawn, 0x6e3adf). Bytes = the sum of the section
data of the map DRM (the memory the loader allocates for the sections, relocation tables not counted).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, 'work', 'sonar_1411b'))
import sonar_floors as F  # noqa: E402

CAP = 300000                     # TruMenu [Sonar] TriangleCap default (0.22.49), the game's own cap is 93572
RATE_MIB = 6.5                   # MiB/s: live loading-screen rate of main units (ENGINE "Level load loop", 11.11.)


def hdr(u):
    return F.header(u + '_map.drm')


def faces(us):
    t = 0
    for u in us:
        h = hdr(u)
        if h: t += h['faces'] - h['skipflag']
    return t


def nbytes(us):
    t = 0
    for u in us:
        e, src, secs = F.sections(u + '_map.drm')
        t += sum(len(s[1] or b'') for s in secs)
    return t


def game_set(start):
    floor, loaded, missing = F.replay(start, False)
    return floor, loaded, missing


def option1(start):
    """the game's set + the portal neighbours of its off-floor members (loaded with recursive 0: no further step)"""
    floor, loaded, missing = game_set(start)
    have = set(loaded) | set(missing)
    extra, extra_missing = [], []
    for u in loaded:
        h = hdr(u)
        if (h['mask'] or 0) & floor:
            continue                     # on-floor units: the game already requested every neighbour
        for name, i4, i8, pos in h['portals']:
            if name in have: continue
            have.add(name)
            if hdr(name) is None: extra_missing.append(name)
            else: extra.append(name)
    return floor, loaded, extra, extra_missing


def option2(start):
    floor, loaded, missing = F.replay(start, True, 10000)
    return floor, loaded, missing


def row(start):
    floor, g, gm = game_set(start)
    _, g1, e1, e1m = option1(start)
    _, a2, a2m = option2(start)
    e2 = [u for u in a2 if u not in g]
    return dict(start=start, floor=floor, g=g, gm=gm, e1=e1, e1m=e1m, a2=a2, e2=e2, a2m=a2m)


def mb(b): return b / 1048576.0


def show(r, detail=True):
    g, e1, a2, e2 = r['g'], r['e1'], r['a2'], r['e2']
    fg, f1, f2 = faces(g), faces(g + e1), faces(a2)
    bg, b1, b2 = nbytes(g), nbytes(g + e1), nbytes(a2)
    print('%-26s floor 0x%02x | game %2d u %6.2f MB %7d f | (1) +%2d u %6.2f MB %7d f%s | (2) +%3d u %6.2f MB %8d f%s'
          ' | extra load ~%.1f s / ~%.1f s at %.1f MiB/s' % (
              r['start'], r['floor'], len(g), mb(bg), fg, len(e1), mb(b1), f1, ' >cap' if f1 > CAP else '',
              len(e2), mb(b2), f2, ' >cap' if f2 > CAP else '', mb(b1 - bg) / RATE_MIB, mb(b2 - bg) / RATE_MIB,
              RATE_MIB))
    if detail:
        print('    game: %s%s' % (', '.join(g), ('; no map file: ' + ', '.join(r['gm'])) if r['gm'] else ''))
        print('    (1) adds: %s%s' % (', '.join(e1) or '-', ('; no map file: ' + ', '.join(r['e1m'])) if r['e1m'] else ''))
        print('    (2) adds: %s%s' % (', '.join(e2) or '-', ('; no map file: ' + ', '.join(r['a2m'])) if r['a2m'] else ''))


def level(prefixes):
    names = [F.unit_of(n) for n in F.M.base_map_names()]
    for p in prefixes:
        us = [u for u in names if u.startswith(p)]
        if not us:
            # DLC names are not in the PC file list: take the given prefix as one start
            us = [p]
        print('=== level %s: %d map units' % (p, len(us)))
        rows = [row(u) for u in us if hdr(u) is not None]
        for r in rows: show(r, detail=False)
        if rows:
            w1 = max(rows, key=lambda r: nbytes(r['g'] + r['e1']))
            w2 = max(rows, key=lambda r: nbytes(r['a2']))
            print('  worst (1): %s' % w1['start']); show(w1)
            print('  worst (2): %s' % w2['start']); show(w2)
        print()


def save_sizes():
    """the reveal entry of a unit in SaveInfo block 6 (0x6df130 -> 0x6ddef0, block 0x3e800 B): key 4 + vertices 4 +
    byte +0x12 1 + u16 +0x10 2 + the run-length bit stream: all bits 0 (a unit never pinged) = one u16 per 16383
    vertices; worst case (alternating bits) = one u16 per 15 vertices"""
    names = [F.unit_of(n) for n in F.M.base_map_names()]
    tot0 = totw = n = 0
    for u in names:
        h = hdr(u)
        if not h: continue
        v = h['verts'] & 0xffff                       # +0xc = (mesh 0 + mesh 1 vertices) as u16 (0x6e2857 movzx)
        tot0 += 11 + 2 * max(1, -(-v // 16383))
        totw += 11 + 2 * max(1, -(-v // 15))
        n += 1
    print('base maps %d: reveal entries if every map got one: never pinged %d B, worst case %d B; block 0x3e800 = %d B'
          % (n, tot0, totw, 0x3e800))


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == 'starts':
        for s in a[1:]: show(row(s))
    elif a[0] == 'level':
        level(a[1:])
    elif a[0] == 'save':
        save_sizes()
    elif a[0] == 'types':                                # section types of the map DRMs (which resolvers get them)
        import collections
        names = [F.unit_of(n) for n in F.M.base_map_names()] + a[1:]
        c = collections.Counter()
        for u in names:
            e, src, secs = F.sections(u + '_map.drm')
            c.update(s[0] for s in secs)
            c['files'] += 1 if secs else 0
        print('section types over %d map DRMs: %s' % (c.pop('files'), dict(sorted(c.items()))))
    else:
        raise SystemExit('unknown mode ' + a[0])
