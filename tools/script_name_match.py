"""Extra id/Symbol mapping pass for Script sections that the fingerprint matcher leaves unmatched (e.g. scripts the PC
patch edited: g_pda's 15 'pda' scripts had NO base id mapping at all).

For every Xbox<->PC DRM pair: unmatched Xbox scripts X and unmatched PC scripts P (after generic_ids.section_matches and
the current id map). The script's ScriptTypeStreamData.m_name Symbol (u16 @ +8) is predicted on PC with the Symbol map
(dlc_generic.DlcIds.sym: map / interpolation / lower-neighbour offset) and paired with the P script whose own name
Symbol is the closest one (|diff| <= 24, unique nearest, both directions) and size within +-35%.
Each accepted pair adds  idmap[8][xid] = pid  and  idmap[100][xsym] = psym  (only where not already mapped and
injective).  Usage: python3 -I tools/script_name_match.py   (rewrites work/generic/idmap.json, backup *_pre_snm.json)
"""
import sys, os, json, struct, collections, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlc_generic as DG
from generic_ids import section_matches
from generic_cache import load_pairs

def symguess(ids, xs):
    """ids.sym, but a lower-neighbour guess that collides is still returned (for nearest-name pairing only)"""
    v = ids.sym(xs)
    if v >= 40000 and v - 40000 == xs:
        import bisect
        k = bisect.bisect_left(ids.sks, xs); a = ids.sks[k - 1]
        v = ids.base[100][a] + xs - a
    return v

def main():
    P = load_pairs(); ids = DG.DlcIds()
    m8 = ids.base[8]; ms = ids.base[100]
    used8 = set(m8.values()); useds = set(ms.values())
    add8 = {}; adds = {}; st = collections.Counter()
    for nm, (x, p) in sorted(P.items()):
        sx, sp = x[1], p[1]
        mt = section_matches(sx, sp, ids.base)
        mx = {i for i, j, _ in mt}; mp = {j for i, j, _ in mt}
        pids = {(s['type'], s['id']) for s in sp}
        X = [s for s in sx if s['type'] == 8 and s['i'] not in mx and s['size'] >= 12 and (8, m8.get(s['id'])) not in pids]
        Q = [s for s in sp if s['type'] == 8 and s['i'] not in mp and s['size'] >= 12 and s['id'] not in used8]
        if not X or not Q: continue
        qs = [(struct.unpack_from('<H', q['data'], 8)[0], q) for q in Q]
        for s in X:
            xs = struct.unpack_from('>H', s['data'], 8)[0]
            pred = symguess(ids, xs)
            c = sorted((abs(ps - pred), ps, q) for ps, q in qs if 0.65 <= q['size'] / s['size'] <= 1.35)
            if not c or c[0][0] > 24 or (len(c) > 1 and c[1][0] == c[0][0]): st['no_unique'] += 1; continue
            d, ps, q = c[0]
            # reverse check: s must be the closest X for q
            back = min((abs(symguess(ids, struct.unpack_from('>H', t['data'], 8)[0]) - ps), t['id']) for t in X)
            if back[1] != s['id']: st['reverse_fail'] += 1; continue
            st['pairs'] += 1; st['exact_sym_pred'] += d == 0
            if s['id'] not in m8 and q['id'] not in used8 and s['id'] not in add8:
                add8[s['id']] = q['id']; used8.add(q['id'])
            if xs not in ms and ps not in useds and xs not in adds:
                adds[xs] = ps; useds.add(ps)
            s['_done'] = True; q['_done'] = True
            if st['shown'] < 30:
                st['shown'] += 1; print('  %-28s X script %5d (%6d B, sym %5d -> pred %5d) <-> PC %5d (%6d B, sym %5d)' % (nm[:28], s['id'], s['size'], xs, pred, q['id'], q['size'], ps))
        # leftovers: same count on both sides, paired in Symbol order when all sizes agree within 10%
        RX = sorted((struct.unpack_from('>H', t['data'], 8)[0], t['id'], t) for t in X if not t.get('_done'))
        RQ = sorted((ps, q['id'], q) for ps, q in qs if not q.get('_done'))
        if RX and len(RX) == len(RQ) and all(0.9 <= q['size'] / t['size'] <= 1.1 for (_, _, t), (_, _, q) in zip(RX, RQ)):
            for (xs, _, t), (ps, _, q) in zip(RX, RQ):
                st['order_pairs'] += 1
                print('  %-28s ORDER  X script %5d (%6d B, sym %5d) <-> PC %5d (%6d B, sym %5d)' % (nm[:28], t['id'], t['size'], xs, q['id'], q['size'], ps))
                if t['id'] not in m8 and q['id'] not in used8 and t['id'] not in add8:
                    add8[t['id']] = q['id']; used8.add(q['id'])
                if xs not in ms and ps not in useds and xs not in adds:
                    adds[xs] = ps; useds.add(ps)
        for t in X + Q: t.pop('_done', None)
    print(dict(st), 'new script ids', len(add8), 'new symbols', len(adds))
    path = os.path.join(DG.W, 'idmap.json')
    shutil.copy(path, path.replace('.json', '_pre_snm.json'))
    d = json.load(open(path))
    for k, v in add8.items(): d['8'][str(k)] = v
    for k, v in adds.items(): d['100'][str(k)] = v
    json.dump(d, open(path, 'w'))
    print('updated', path)

if __name__ == '__main__':
    main()
