"""End-to-end validation of the generic converter (dlc_generic.convert_drm, route 'convert' only — pc_copy and
template would trivially copy PC data on base pairs) against the Xbox<->PC base pairs.

Per type: equal-size matched sections, exact, exact-modulo-order (all wrong words lie on id-ref offsets and
each maximal run of consecutive id-ref words holds the same multiset), reloc blob exact, wrong-word rate.
Also checks the assembled DRM: section count/types/flags/spec/ids vs the PC DRM (ids via section match).
Usage: python3 -I tools/generic_validate.py [step]   (every step-th pair DRM; default 1)
"""
import sys, os, struct, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R
import dlc_generic as DG
from generic_ids import section_matches
from generic_cache import load_pairs
import generic_store

def runs(offs):
    offs = sorted(offs); out = []; cur = []
    for o in offs:
        if cur and o != cur[-1] + 4: out.append(cur); cur = []
        cur.append(o)
    if cur: out.append(cur)
    return out

def mod_order_equal(d, p, rel):
    io = rel.id_offsets()
    bad = [w for w in range(0, len(d) // 4 * 4, 4) if d[w:w + 4] != p[w:w + 4]]
    if any(w not in io for w in bad) or d[len(d) // 4 * 4:] != p[len(p) // 4 * 4:]: return False
    for r in runs(io):
        if sorted(d[o:o + 4] for o in r) != sorted(p[o:o + 4] for o in r): return False
    return True

REAUTH = '--reauthored' in sys.argv     # default OFF: pure conversion

def main(step=1, types=(0, 2, 7, 8, 11, 13)):
    P = load_pairs(); store = generic_store.load(); ids = DG.DlcIds(); T = DG.table()
    st = collections.Counter()
    for nm in sorted(P)[::step]:
        x, p = P[nm]; sx, sp = x[1], p[1]
        secs, rep = DG.convert_drm(sx, ids, store, T=T, use_pc_copy=False, use_template=False, use_pc_reauthored=REAUTH)
        st['drm'] += 1
        st['drm_sections_equal_count'] += len(secs) == len(sp)
        for i, j, _ in section_matches(sx, sp, ids.base):
            a, b, c = sx[i], sp[j], secs[i]
            t = a['type']
            st[t, 'id_ok'] += c.id == b['id']; st[t, 'matched'] += 1
            st[t, 'hdr_ok'] += (c.type, c.flags, c.spec) == (b['type'], b['flags'], b['spec'])
            if t not in types or a['size'] != b['size'] or b['data'] is None: continue
            st[t, 'n'] += 1; st[t, 'bytes'] += a['size']
            st[t, 'reloc_ok'] += c.reloc == b['reloc']
            if c.data == b['data']: st[t, 'exact'] += 1; st[t, 'modorder'] += 1
            else:
                st[t, 'badw'] += sum(1 for w in range(0, len(c.data), 4) if c.data[w:w + 4] != b['data'][w:w + 4])
                st[t, 'modorder'] += mod_order_equal(c.data, b['data'], R.parse(a['reloc'], 'be'))
    print('DRMs %d, same section count %d' % (st['drm'], st['drm_sections_equal_count']))
    for t in sorted({k[0] for k in st if isinstance(k, tuple)}):
        n = st[t, 'n']
        line = 'type %2d: matched %6d id_ok %6.2f%% hdr_ok %6.2f%%' % (t, st[t, 'matched'], 100. * st[t, 'id_ok'] / st[t, 'matched'], 100. * st[t, 'hdr_ok'] / st[t, 'matched'])
        if n:
            line += ' | equal-size %6d exact %6.2f%% exact-mod-order %6.2f%% reloc %6.2f%% wrong words %.3f%%' % (
                n, 100. * st[t, 'exact'] / n, 100. * st[t, 'modorder'] / n, 100. * st[t, 'reloc_ok'] / n, 400. * st[t, 'badw'] / max(1, st[t, 'bytes']))
        print(line)
    print('symbol stats', dict(ids.sym_stats), 'ids missing', dict(ids.missing))
    return st

if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if not x.startswith('--')]
    main(int(a[0]) if a else 1)
