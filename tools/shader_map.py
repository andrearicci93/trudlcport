"""DLC ShaderLib (type 9) -> PC ShaderLib id map, with a fallback for DLC shaders that have no PC counterpart.

Xenos microcode can't be ported, so every DLC shader id is mapped to an EXISTING PC shader id:
  A  id exists in the Xbox base (bytes identical, verified 505/505)        -> shader_x2p[id]
  B  same content as a base Xbox lib under another id                     -> shader_x2p[base id]
  C1/C2/C3/D  no identical base lib: choose a surrogate base Xbox lib (Xbox-vs-Xbox comparison: same compiler,
     same CTAB format) and map through shader_x2p. The surrogate is chosen at MATERIAL level: for each new DLC
     material the base Xbox material with the best summed per-lib similarity over its 4-shader tuple
     (slots 0-2 = pixel-shader libs per pass, slot 3 = vertex-shader lib) is taken, so the resulting PC
     (VS, PS) pairs are pairs PC actually ships. Per DLC lib, the PC id is the majority vote over its materials
     (libs used by no new material: best per-lib match).
  Per-lib similarity (0..1) between Xbox libs (hard constraints: same kind; VS: base occupied permutation slots
  must cover the DLC lib's): 0.4 * Jaccard(slot blob hashes) + 0.3 * J(constants (name#,regset,reg,count))
  + 0.2 * J(sampler (name#, reg)) + 0.1 * J(sampler regs).   name# = name with hash parts stripped.
  The class letter (C1 strict constant signature, C2 sampler-name signature, C3 sampler-register signature,
  D none) is the previous agent's classification and only describes how close a match exists.
Outputs: work/render/dlc_shader_map.json, work/render/shader_map.txt (report incl. leave-one-out on base).
usage: tools/venv/bin/python -I tools/shader_map.py"""
import sys, os, pickle, struct, collections, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shaderlib import parse, constants, norm_name, slot_hashes
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work', 'render')

def load_libs():
    cache = os.path.join(W, 'shaderlibs.pkl')
    if os.path.exists(cache): return pickle.load(open(cache, 'rb'))
    res = pickle.load(open(os.path.join(W, 'pairs_render.pkl'), 'rb'))
    dlc = pickle.load(open(os.path.join(W, 'dlc_render.pkl'), 'rb'))
    X, P, D, XM, PM, DM = {}, {}, {}, {}, {}, {}
    for nm, XS, PS in res:
        for a in XS:
            if a['type'] == 9 and a['id'] not in X: X[a['id']] = parse(a['data'], 'be')
            if a['type'] == 10 and a['id'] not in XM: XM[a['id']] = (a['data'], a['reloc'])
        for b in PS:
            if b['type'] == 9 and b['id'] not in P: P[b['id']] = parse(b['data'], 'le')
            if b['type'] == 10 and b['id'] not in PM: PM[b['id']] = (b['data'], b['reloc'])
    for path, i, h, secs in dlc:
        for s in secs or []:
            if s['type'] == 9 and s['id'] not in D: D[s['id']] = parse(s['data'], 'be')
            if s['type'] == 10 and s['id'] not in DM: DM[s['id']] = (s['data'], s['reloc'])
    out = dict(X=X, P=P, D=D, XM=XM, PM=PM, DM=DM)
    pickle.dump(out, open(cache, 'wb'))
    return out

def features(lib, pl='x'):
    occ = frozenset(i for i, s in enumerate(lib['slots']) if s != 0xFFFFFFFF)
    blobs = frozenset(h for h in slot_hashes(lib) if h)
    strict, sname, sreg = set(), set(), set()
    per_slot = []
    for s in lib['slots']:
        if s == 0xFFFFFFFF: per_slot.append(None); continue
        v, c = constants(lib['entries'][s]['blob'], pl)
        per_slot.append(c)
        for n, rs, ri, rc in c:
            nn = norm_name(n); strict.add((nn, rs, ri, rc))
            if rs == 3: sname.add((nn, ri)); sreg.add(ri)
    sig_strict = tuple(None if c is None else tuple(sorted((norm_name(n), rs, ri, rc) for n, rs, ri, rc in c)) for c in per_slot)
    sig_sname = tuple(None if c is None else tuple(sorted((norm_name(n), ri) for n, rs, ri, rc in c if rs == 3)) for c in per_slot)
    sig_sreg = tuple(None if c is None else tuple(sorted(ri for n, rs, ri, rc in c if rs == 3)) for c in per_slot)
    return dict(kind=lib['kind'], occ=occ, blobs=blobs, strict=frozenset(strict), sname=frozenset(sname), sreg=frozenset(sreg),
                content=(lib['kind'], tuple(slot_hashes(lib))), sig=dict(strict=(lib['kind'], sig_strict), samplers=(lib['kind'], sig_sname), regs=(lib['kind'], sig_sreg)))

def J(a, b):
    return len(a & b) / len(a | b) if (a or b) else 1.0

def sim(fd, fb):
    if fd['kind'] != fb['kind']: return -1.0
    if fd['content'] == fb['content']: return 1.0
    if fd['kind'] == 0 and not fd['occ'] <= fb['occ']:
        return -0.5 + 0.5 * len(fd['occ'] & fb['occ']) / max(1, len(fd['occ']))   # coverage violation: last resort only
    return 0.4 * J(fd['blobs'], fb['blobs']) + 0.3 * J(fd['strict'], fb['strict']) + 0.2 * J(fd['sname'], fb['sname']) + 0.1 * J(fd['sreg'], fb['sreg'])

def classify(fd, sid, X, content_idx, sig_idx):
    if sid in X: return 'A'
    if fd['content'] in content_idx: return 'B'
    for lv, tag in (('strict', 'C1'), ('samplers', 'C2'), ('regs', 'C3')):
        if fd['sig'][lv] in sig_idx[lv]: return tag
    return 'D'

def tuple_of(d, e='>'):
    return struct.unpack_from(e + '4I', d, 0x28)

def vs_inputs(d, r, e='>'):
    """Per-pass VS input semantic lists of a material (ptrs at 0x08/0x0C/0x10 -> {0,0,n,pass, n x 28B {u32 sem,..}}).
    Xbox == PC lists for 2233/2247 base material pairs (material_convert copies them)."""
    import drm_reloc as R
    ptr = dict(R.parse(r, 'be' if e == '>' else 'le').internal); out = []
    for f in (0x08, 0x0C, 0x10):
        T = ptr.get(f)
        if T is None: out.append(None); continue
        n = struct.unpack_from(e + 'I', d, T + 8)[0]
        out.append(tuple(struct.unpack_from(e + 'I', d, T + 16 + 28 * k)[0] for k in range(n)))
    return tuple(out)

def main():
    L = load_libs(); X, P, D, XM, PM, DM = L['X'], L['P'], L['D'], L['XM'], L['PM'], L['DM']
    x2p = pickle.load(open(os.path.join(W, 'shader_x2p.pkl'), 'rb'))
    mx2p = pickle.load(open(os.path.join(W, 'material_x2p.pkl'), 'rb'))
    FX = {k: features(l) for k, l in X.items()}
    FD = {k: (FX[k] if k in FX else features(l)) for k, l in D.items()}
    base = [k for k in X if k in x2p]
    content_idx = {}
    for k in sorted(base): content_idx.setdefault(FX[k]['content'], k)
    sig_idx = {lv: collections.defaultdict(list) for lv in ('strict', 'samplers', 'regs')}
    for k in sorted(base):
        for lv in sig_idx: sig_idx[lv][FX[k]['sig'][lv]].append(k)
    cls = {k: classify(FD[k], k, X, content_idx, sig_idx) for k in D}
    # tuple position(s) a lib is used at (0-2 pixel-shader passes, 3 vertex shader). PC re-slots pixel-shader libs
    # by position (pos0 -> 4 slots, pos1 -> 2, pos2 -> 8; verified on all base PC materials), so surrogates must
    # come from the same position.
    xpos = collections.defaultdict(set); dpos = collections.defaultdict(set)
    for mid, (d, r) in XM.items():
        for i, s_ in enumerate(tuple_of(d)):
            if s_: xpos[s_].add(i)
    for mid, (d, r) in DM.items():
        for i, s_ in enumerate(tuple_of(d)):
            if s_: dpos[s_].add(i)
    simc = {}
    def S(d, b):
        if d == b: return 1.0
        k = (d, b)
        if k not in simc: simc[k] = sim(FD[d] if d in FD else FX[d], FX[b])
        return simc[k]
    # exact part of the map
    out = {}
    for k in D:
        if cls[k] == 'A': out[k] = dict(pc=x2p.get(k), cls='A', basis='same id in base', surrogate=k)
        elif cls[k] == 'B':
            b = content_idx[FD[k]['content']]
            out[k] = dict(pc=x2p[b], cls='B', basis='identical content as base id %d' % b, surrogate=b)
    # ---- material-level surrogate choice
    base_mats = []
    for mid, (d, r) in XM.items():
        if mid in mx2p and mx2p[mid] in PM:
            t = tuple_of(d)
            if all(s == 0 or s in x2p for s in t): base_mats.append((mid, t, struct.unpack_from('>I', d, 0x58)[0]))
    by_pattern = collections.defaultdict(list)
    for mid, t, npar in base_mats:
        by_pattern[tuple((0 if s == 0 else X[s]['kind']) for s in t)].append((mid, t, npar))
    pc_pairs = set()
    for mid, t, npar in base_mats:
        pt = tuple_of(PM[mx2p[mid]][0], '<')
        for ps in pt[:3]:
            if ps: pc_pairs.add((pt[3], ps))
    votes = collections.defaultdict(collections.Counter); mat_choice = {}
    newmats = [(mid, d) for mid, (d, r) in DM.items() if mid not in XM]
    for mid, d in newmats:
        t = tuple_of(d)
        if all(s == 0 or cls.get(s) in ('A', 'B') for s in t):
            continue
        pat = tuple((0 if s == 0 else D[s]['kind'] if s in D else X[s]['kind']) for s in t)
        npar = struct.unpack_from('>I', d, 0x58)[0]
        vs_sur = t[3] != 0 and cls.get(t[3]) not in ('A', 'B')
        din = vs_inputs(d, DM[mid][1])
        best = None
        for bmid, bt, bnpar in by_pattern.get(pat, []):
            sc = 0.0
            for s, b in zip(t, bt):
                if s == 0: continue
                sb = out[s]['surrogate'] if s in out else s
                sc += 1.0 if sb == b else S(s, b)
            sc += 0.3 * (bnpar == npar)
            if vs_sur:   # surrogate VS must not need vertex inputs the DLC material/mesh doesn't provide
                bin_ = vs_inputs(*XM[bmid])
                sc += 3.0 if bin_ == din else (2.0 if all(b is None or (a is not None and set(b) <= set(a)) for a, b in zip(din, bin_)) else 0.0)
            ptup = [0 if s == 0 else (out[s]['pc'] if s in out else x2p[b]) for s, b in zip(t, bt)]
            sc += 0.5 * all((ptup[3], ps) in pc_pairs for ps in ptup[:3] if ps)
            if best is None or sc > best[0]: best = (sc, bmid, bt, ptup)
        if best is None: continue
        mat_choice[mid] = best
        for s, b in zip(t, best[2]):
            if s and s not in out: votes[s][b] += 1
    # ---- per-lib decision for C/D libs
    for k in D:
        if k in out: continue
        if votes.get(k):
            b, n = votes[k].most_common(1)[0]
            out[k] = dict(pc=x2p[b], cls=cls[k], basis='material-level vote %d/%d' % (n, sum(votes[k].values())), surrogate=b, score=round(S(k, b), 3))
        else:
            cand = [b for b in base if FX[b]['kind'] == FD[k]['kind'] and (not dpos[k] or dpos[k] & xpos[b])]
            b = max(cand, key=lambda b: (S(k, b), -b))
            out[k] = dict(pc=x2p[b], cls=cls[k], basis='best per-lib match (no new material uses it)', surrogate=b, score=round(S(k, b), 3))
        # candidates with the same signature as in classification
        lv = {'C1': 'strict', 'C2': 'samplers', 'C3': 'regs'}.get(cls[k])
        out[k]['sig_candidates'] = len(sig_idx[lv][FD[k]['sig'][lv]]) if lv else 0
        out[k]['vs_slot_coverage_ok'] = FD[k]['kind'] != 0 or FD[k]['occ'] <= FX[out[k]['surrogate']]['occ']
    # ---- report
    lines = []
    cc = collections.Counter(v['cls'] for v in out.values())
    lines.append('DLC shader libs: %d  by class %s' % (len(out), dict(sorted(cc.items()))))
    lines.append('unmapped (no PC id): %d' % sum(1 for v in out.values() if v['pc'] is None))
    sc = collections.defaultdict(list)
    for k, v in out.items():
        if 'score' in v: sc[v['cls']].append(v['score'])
    for c_, l in sorted(sc.items()):
        l.sort(); lines.append('  class %s surrogate similarity: n=%d min %.3f median %.3f' % (c_, len(l), l[0], l[len(l) // 2]))
    lines.append('  VS coverage violations: %d' % sum(1 for v in out.values() if v.get('vs_slot_coverage_ok') is False))
    # consistency: resulting PC (VS,PS) pairs of new DLC materials that exist in base PC materials
    ok = tot = 0; okm = totm = 0
    for mid, d in newmats:
        t = tuple_of(d); pt = [out[s]['pc'] if s else 0 for s in t]
        prs = [(pt[3], ps) for ps in pt[:3] if ps]
        good = all(p in pc_pairs for p in prs)
        okm += good; totm += 1
        ok += sum(p in pc_pairs for p in prs); tot += len(prs)
    lines.append('new DLC materials: %d; materials whose every PC (VS,PS) pass pair exists in some base PC material: %d (%.1f%%); pairs %d/%d' % (totm, okm, 100.0 * okm / max(1, totm), ok, tot))
    # per-material PC tuples (material-specific surrogates; A/B libs always exact)
    mt = {}
    okm2 = 0; vsin = collections.Counter()
    for mid, d in newmats:
        t = tuple_of(d)
        if mid in mat_choice: ptup = mat_choice[mid][3]
        else: ptup = [out[s]['pc'] if s else 0 for s in t]
        vs_sur = t[3] != 0 and cls.get(t[3]) not in ('A', 'B')
        if mid in mat_choice:
            a_, b_ = vs_inputs(d, DM[mid][1]), vs_inputs(*XM[mat_choice[mid][1]])
            inp_eq = 'equal' if a_ == b_ else ('surrogate subset' if all(y is None or (x is not None and set(y) <= set(x)) for x, y in zip(a_, b_)) else 'surrogate needs more')
        else: inp_eq = 'equal'
        vsin[('VS surrogate' if vs_sur else 'VS exact', inp_eq)] += 1
        mt[str(mid)] = dict(pc_tuple=ptup, vs_surrogate=vs_sur, vs_inputs_equal_surrogate=inp_eq,
                            base_material=(mat_choice[mid][1] if mid in mat_choice else None),
                            score=(round(mat_choice[mid][0], 3) if mid in mat_choice else None))
        okm2 += all((ptup[3], ps) in pc_pairs for ps in ptup[:3] if ps)
    lines.append('with per-material tuples (work/render/dlc_material_shaders.json): %d/%d (%.1f%%) materials have only shipped PC (VS,PS) pairs' % (okm2, len(newmats), 100.0 * okm2 / max(1, len(newmats))))
    lines.append('VS input lists (DLC material vs surrogate base material; matters only when the VS is a surrogate): %s' % dict(sorted(vsin.items())))
    json.dump(mt, open(os.path.join(W, 'dlc_material_shaders.json'), 'w'), indent=0)
    json.dump({str(k): v for k, v in sorted(out.items())}, open(os.path.join(W, 'dlc_shader_map.json'), 'w'), indent=0)
    open(os.path.join(W, 'shader_map.txt'), 'w').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    return L, FX, FD, x2p, base, sig_idx, out, xpos

def loo(L, FX, x2p, base, sig_idx, xpos):
    """Leave-one-out on base: hide each mapped base Xbox lib, pick the best other base lib (excluding identical
    content) by the same similarity, compare PC ids (exact) and PC-side signatures (strict / sampler names)."""
    P = L['P']
    FP = {}
    def fp(pid):
        if pid not in FP: FP[pid] = features(P[pid], 'p')
        return FP[pid]
    st = collections.Counter()
    bykind = collections.defaultdict(list)
    for b in base: bykind[FX[b]['kind']].append(b)
    for k in base:
        f = FX[k]
        # class this lib would get against the others
        lvl = 'D'
        for lv, tag in (('strict', 'C1'), ('samplers', 'C2'), ('regs', 'C3')):
            if len([b for b in sig_idx[lv][f['sig'][lv]] if b != k and FX[b]['content'] != f['content']]) > 0: lvl = tag; break
        okpos = lambda b: not xpos[k] or bool(xpos[k] & xpos[b])
        cand = [b for b in bykind[f['kind']] if b != k and FX[b]['content'] != f['content'] and okpos(b)]
        if lvl != 'D':
            lv = {'C1': 'strict', 'C2': 'samplers', 'C3': 'regs'}[lvl]
            c2 = [b for b in sig_idx[lv][f['sig'][lv]] if b != k and FX[b]['content'] != f['content'] and okpos(b)]
            cand = c2 or cand
        if not cand: st[lvl, 'no candidate'] += 1; continue
        best = max(cand, key=lambda b: (sim(f, FX[b]), -b))
        tp, cp = x2p[k], x2p[best]
        st[lvl, 'n'] += 1
        st[lvl, 'same PC id'] += tp == cp
        st[lvl, 'same PC strict sig'] += fp(tp)['sig']['strict'] == fp(cp)['sig']['strict']
        st[lvl, 'same PC sampler-name sig'] += fp(tp)['sig']['samplers'] == fp(cp)['sig']['samplers']
        st[lvl, 'same PC sampler set'] += fp(tp)['sname'] == fp(cp)['sname']
        st[lvl, 'PC slots cover'] += fp(tp)['occ'] <= fp(cp)['occ']
    lines = ['leave-one-out on %d mapped base Xbox libs (surrogate chosen among other base libs with the same signature level):' % len(base)]
    for lvl in ('C1', 'C2', 'C3', 'D'):
        n = st[lvl, 'n']
        if not n: continue
        lines.append('  %s n=%d same PC id %d (%.0f%%), same PC strict sig %d (%.0f%%), same PC sampler-name sig %d (%.0f%%), same PC sampler set %d (%.0f%%), PC slot cover %d (%.0f%%)' % (
            lvl, n, st[lvl, 'same PC id'], 100.0 * st[lvl, 'same PC id'] / n, st[lvl, 'same PC strict sig'], 100.0 * st[lvl, 'same PC strict sig'] / n,
            st[lvl, 'same PC sampler-name sig'], 100.0 * st[lvl, 'same PC sampler-name sig'] / n, st[lvl, 'same PC sampler set'], 100.0 * st[lvl, 'same PC sampler set'] / n,
            st[lvl, 'PC slots cover'], 100.0 * st[lvl, 'PC slots cover'] / n))
    return lines

if __name__ == '__main__':
    L, FX, FD, x2p, base, sig_idx, out, xpos = main()
    lines = loo(L, FX, x2p, base, sig_idx, xpos)
    print('\n'.join(lines))
    open(os.path.join(W, 'shader_map.txt'), 'a').write('\n'.join(lines) + '\n')
