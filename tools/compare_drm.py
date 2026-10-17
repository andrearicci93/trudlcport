"""Compare a converted PC DRM (ours) with the real PC DRM, per section type: data exact / reloc exact.
Sections are paired by fingerprint (type, size, reloc bytes, internal reloc list; unique), then by (type, id) for
non-General types, then positionally inside equal (type,size,reloc-size) groups (generic_ids.section_matches on LE).
Reloc blobs are compared NORMALISED: external entries as (target type, target id, src, dst) - the section index differs
legitimately when the section order differs.  For General (type 0, all id 0) the target is (0, index-in-type-0-order).
usage: tools/venv/bin/python -I tools/compare_drm.py OURS.drm NAME.drm [--words]   (NAME looked up in pc/bigfile)
"""
import sys, os, collections, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R
from drm import cdrm_decode, sections_with_data

def section_matches(so, sp):
    MEDIA = (5, 6, 9, 10, 12)
    def fp(s): return (s['type'], s['size'], len(s['reloc']), tuple(R.parse(s['reloc'], 'le').internal)) if s['type'] not in MEDIA else None
    out = []; uo = set(); up = set()
    go = collections.defaultdict(list); gp = collections.defaultdict(list)
    for s in so:
        f = fp(s)
        if f: go[f].append(s['i'])
    for s in sp:
        f = fp(s)
        if f: gp[f].append(s['i'])
    for k, l in go.items():
        if len(l) == 1 and len(gp.get(k, ())) == 1: out.append((l[0], gp[k][0], 'A')); uo.add(l[0]); up.add(gp[k][0])
    pid = {(s['type'], s['id']): s['i'] for s in sp if s['type'] != 0 and s['i'] not in up}
    for s in so:
        if s['i'] in uo or s['type'] == 0: continue
        j = pid.pop((s['type'], s['id']), None)
        if j is not None: out.append((s['i'], j, 'K')); uo.add(s['i']); up.add(j)
    go = collections.defaultdict(list); gp = collections.defaultdict(list)
    for s in so:
        if s['i'] not in uo: go[s['type'], s['size'] if s['type'] not in MEDIA else 0, len(s['reloc'])].append(s['i'])
    for s in sp:
        if s['i'] not in up: gp[s['type'], s['size'] if s['type'] not in MEDIA else 0, len(s['reloc'])].append(s['i'])
    for k, l in go.items():
        m = gp.get(k, [])
        if len(l) == len(m): out += [(a, b, 'C') for a, b in zip(l, m)]
    return out

def load(raw):
    h, s = sections_with_data(cdrm_decode(raw, 'le'), 'le')
    return s

def norm_reloc(s, secs):
    r = R.parse(s['reloc'], 'le')
    t0 = {}
    for x in secs:
        if x['type'] == 0: t0[x['i']] = len(t0)
    ext = [((secs[si]['type'], secs[si]['id'] if secs[si]['type'] != 0 else t0[si]), so, do) for si, so, do in r.external]
    return (r.internal, ext, r.idref, r.idref_a)

def compare(ours, pc, words=False, out=sys.stdout):
    so, sp = load(ours), load(pc)
    m = section_matches(so, sp)
    for a in so: a['_e'] = 'le'
    st = collections.Counter(); bad = []
    matched_o = {i for i, _, _ in m}
    for i, j, how in m:
        a, b = so[i], sp[j]
        t = a['type']
        st[t, 'matched'] += 1
        de = a['data'] == b['data']; re_ = norm_reloc(a, so) == norm_reloc(b, sp)
        st[t, 'data_exact'] += de; st[t, 'reloc_exact'] += re_
        if not de:
            nw = sum(1 for k in range(0, len(a['data']), 4) if a['data'][k:k + 4] != b['data'][k:k + 4])
            st[t, 'bad_words'] += nw
            bad.append((t, i, j, a['id'], len(a['data']), nw, re_))
        elif not re_:
            bad.append((t, i, j, a['id'], len(a['data']), 0, re_))
    st['unmatched_ours'] = len(so) - len(matched_o)
    for t in sorted({k[0] for k in st if isinstance(k, tuple)}):
        print('type %2d: matched %5d  data exact %5d  reloc exact %5d  wrong words %d' % (
            t, st[t, 'matched'], st[t, 'data_exact'], st[t, 'reloc_exact'], st[t, 'bad_words']), file=out)
    print('unmatched sections (ours):', st['unmatched_ours'], 'of', len(so), '; pc', len(sp), file=out)
    if words:
        for t, i, j, sid, n, nw, re_ in bad:
            print('  type %d ours#%d pc#%d id %d size %d wrong words %d reloc %s' % (t, i, j, sid, n, nw, 'ok' if re_ else 'DIFF'), file=out)
    return st, bad

if __name__ == '__main__':
    from rung1 import raw_pc
    ours = open(sys.argv[1], 'rb').read()
    compare(ours, raw_pc(sys.argv[2]), '--words' in sys.argv)
