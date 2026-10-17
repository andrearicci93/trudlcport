"""Build Xbox-id -> PC-id maps per section type from the base-game DRM pairs.

Evidence (in decreasing strength):
  A  section matched by unique fingerprint (type,size,reloc bytes,internal reloc list) inside a DRM pair
  B  id-reference votes: for A-matched sections whose idref lists are identical, X value vs PC value
     at the same data offset (noisy: some id lists are permuted between platforms)
  C  positional match inside a (type,size,reloc-size) group once A/B-known ids are removed, or for
     media types (size differs) positional match in the per-type sequence
Final map = for each (type,xid) the PC id with most weighted votes (A=100, C=10, B=1).
Writes work/generic/idmap.json  {type: {xid: pid}} and prints consistency statistics.
"""
import sys, os, pickle, struct, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'generic')
MEDIA = (5, 6, 9, 10, 12)

def fp(s, e):
    if s['type'] in MEDIA: return (s['type'],)
    r = R.parse(s['reloc'], e)
    return (s['type'], s['size'], len(s['reloc']), tuple(r.internal))

def loose(s):
    if s['type'] in MEDIA: return (s['type'],)
    return (s['type'], s['size'], len(s['reloc']))

def section_matches(sx, sp, known=None):
    """Return list of (xbox_index, pc_index, strength) for one DRM pair."""
    out = []; used_x = set(); used_p = set()
    gx = collections.defaultdict(list); gp = collections.defaultdict(list)
    for s in sx: gx[fp(s, 'be')].append(s['i'])
    for s in sp: gp[fp(s, 'le')].append(s['i'])
    for k, l in gx.items():
        m = gp.get(k, [])
        if len(l) == 1 and len(m) == 1 and k[0] not in MEDIA:
            out.append((l[0], m[0], 'A')); used_x.add(l[0]); used_p.add(m[0])
    if known:
        pid2i = {(s['type'], s['id']): s['i'] for s in sp if s['i'] not in used_p}
        for s in sx:
            if s['i'] in used_x: continue
            pid = known.get(s['type'], {}).get(s['id'])
            j = pid2i.get((s['type'], pid))
            if j is not None and loose(sp[j]) == loose(s):
                out.append((s['i'], j, 'K')); used_x.add(s['i']); used_p.add(j); del pid2i[(s['type'], pid)]
    gx = collections.defaultdict(list); gp = collections.defaultdict(list)
    for s in sx:
        if s['i'] not in used_x: gx[loose(s)].append(s['i'])
    for s in sp:
        if s['i'] not in used_p: gp[loose(s)].append(s['i'])
    for k, l in gx.items():
        m = gp.get(k, [])
        if len(l) == len(m):
            out += [(a, b, 'C') for a, b in zip(l, m)]
    return out

def build(P, known=None):
    votes = collections.defaultdict(collections.Counter)
    for nm, (x, p) in P.items():
        sx, sp = x[1], p[1]
        for i, j, st in section_matches(sx, sp, known):
            a, b = sx[i], sp[j]
            votes[a['type'], a['id']][b['id']] += {'A': 100, 'K': 50, 'C': 10}[st]
            if st == 'A' and a['data'] is not None and b['data'] is not None:
                ra, rb = R.parse(a['reloc'], 'be'), R.parse(b['reloc'], 'le')
                if ra.idref != rb.idref or ra.idref_a != rb.idref_a: continue
                for t, o in ra.idref + ra.idref_a:
                    v, = struct.unpack('>I', a['data'][o:o + 4]); w, = struct.unpack('<I', b['data'][o:o + 4])
                    votes[t, v][w] += 1
    return votes

def resolve(votes):
    m = collections.defaultdict(dict); stats = collections.Counter()
    for (t, xid), c in votes.items():
        (pid, n), = c.most_common(1)
        tot = sum(c.values())
        m[t][xid] = pid
        stats[t, 'ids'] += 1
        if n < tot: stats[t, 'contested'] += 1
        if n * 2 <= tot: stats[t, 'weak(<=50%)'] += 1
    # injectivity: several Xbox ids voting for one PC id (verified: their Xbox contents DIFFER in 38/40 cases)
    # -> keep only the Xbox id with the strongest vote for that PC id, the others become unmapped (= DLC-new ids)
    for t, d in m.items():
        inv = collections.defaultdict(list)
        for xid, pid in d.items(): inv[pid].append(xid)
        for pid, xs in inv.items():
            if len(xs) > 1:
                stats[t, 'non_injective_dropped'] += len(xs) - 1
                keep = max(xs, key=lambda x: (votes[t, x][pid], -x))
                for x in xs:
                    if x != keep: del d[x]
    return m, stats

if __name__ == '__main__':
    from generic_cache import load_pairs
    P = load_pairs()
    m, st = resolve(build(P))
    m2, st2 = resolve(build(P, m))      # second pass with known ids to unlock ambiguous groups
    for k, v in sorted(st2.items()): print(k, v)
    # coverage: fraction of Xbox sections (in pair DRMs) whose id is mapped
    cov = collections.Counter()
    for nm, (x, p) in P.items():
        for s in x[1]:
            cov[s['type'], 'mapped' if s['id'] in m2[s['type']] else 'unmapped'] += 1
    for k, v in sorted(cov.items()): print('coverage', k, v)
    out = {str(t): {str(a): b for a, b in d.items()} for t, d in m2.items()}
    path = os.path.join(W, 'idmap.json')
    if os.path.exists(path):                       # keep the Symbol map (key 100, built by generic_symbols)
        old = json.load(open(path))
        if '100' in old: out['100'] = old['100']
    json.dump(out, open(path, 'w'))
    print('wrote idmap.json')
