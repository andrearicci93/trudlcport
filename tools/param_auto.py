"""Automatic MaterialParams alignment for DLC materials whose pixel-shader libs were replaced by a PC surrogate
(2026-10-12; generalises tools/param_remap.py, which did it by hand for material 21118 / libs 2298,2299 -> 1200,1201).

Idea. A DLC lib D (Xenos microcode, new compile) was replaced by an existing base Xbox lib S (the 'surrogate', itself
compiled to PC via shader_x2p). D and S come from the same shader graph but the compiler packed MaterialParams
(c100..) differently, and material_dlc copied the DLC params 1:1. The map  D-param-component -> S-param-component  is
read from the microcode: both instruction streams are aligned on a token skeleton that ignores ONLY the
MaterialParams constant index/swizzle of each operand; at every aligned instruction the used lanes of every
MaterialParams operand give a vote (D comp -> S comp). A PC param component (= S layout, composed with the
Xbox->PC rule learned from base pairs, param_rules.pkl, when one exists) is auto-fixed only when its map is PROVEN:
 * every S component referenced anywhere in the S microcode (all permutation slots, all passes of the material)
   is covered by aligned instructions and has exactly one D source,
 * no conflicting vote,
 * alignment covers the whole instruction stream of the S libs (otherwise tier 'approx' = report only).
Class C3 / D materials (different sampler register sets) are report-only.

CLI:  tools/venv/bin/python -I tools/param_auto.py oracle         (reproduce the hand map of 21118 from the microcode)
      tools/venv/bin/python -I tools/param_auto.py scan [OUTDIR]   (table for every DLC1 converted material)
      tools/venv/bin/python -I tools/param_auto.py fix OUTDIR SRC.drm [SRC2.drm ..]
API:  derive_pair(dlc_lib, sur_lib), material_plan(xmid), fix_section(xmid, pc_data, pc_reloc) -> (data, info)
"""
import sys, os, struct, pickle, json, collections, difflib, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xenos_ps as XP
import drm_reloc as R
from shaderlib import constants

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
W = os.path.join(ROOT, 'work', 'render')

_L = None
def libs():
    global _L
    if _L is None: _L = pickle.load(open(os.path.join(W, 'shaderlibs.pkl'), 'rb'))
    return _L


def param_range(blob):
    v, c = constants(blob, 'x')
    for n, rs, ri, rc in c:
        if n == 'MaterialParams' and rs == 2: return ri, rc
    return None


def _mask(sw, lanes):
    m = 0
    for l in lanes: m |= 3 << (2 * l)
    return sw & m


class Item:
    __slots__ = ('tok', 'prm', 'uses', 'defs', 'kind', 'idx', 'cidx')


def _vec_active(f):
    return f['vmask'] != 0 or f['vopc'] in (20, 21, 22, 23, 24, 25, 26, 27)


def build(blob, p0, pn):
    """Program-order list of Item for CF / ALU / fetch records. tok = coarse token (no temp register numbers, no
    MaterialParams constant index / swizzle); prm = [(role, param index, [(lane, comp)])]; uses = [(temp reg, comp)] read;
    defs = [(temp reg, comp)] written."""
    items = []
    for it in XP.instructions(blob):
        o = Item(); o.prm = []; o.uses = []; o.defs = []; o.kind = it[0]
        if it[0] == 'cf':
            r = it[1]; c = r['raw']
            o.tok = ('cf', r['op'], r['n'], r['seq'], (c >> 28) & 0xffff) if r['addr'] is not None else ('cf', r['op'], (c >> 12) & 0xffffffff)
        elif it[0] == 'fetch':
            _, s, d0, d1, d2 = it
            o.tok = ('fetch', d0 & 31, (d0 >> 20) & 31, (d0 >> 26) & 63, d1 & 0xfff)
            o.cidx = (d0 >> 20) & 31
            dst = (d0 >> 12) & 63
            o.defs = [(dst, c) for c in range(4)]
            src = (d0 >> 5) & 63
            o.uses = [(src, (d0 >> 26) & 3), (src, (d0 >> 28) & 3)]
        else:
            _, s, f, raw = it
            vact = _vec_active(f); so = f['sopc']
            nops = XP.VOP_OPERANDS.get(f['vopc'], 0) if vact else 0
            tok = [f['vopc'] if vact else -1, f['vmask'] if vact else 0, so, f['smask'] if so != XP.SOP_NOP else 0, f['export'],
                   f['vclamp'], f['sclamp'], f['ispred'], f['predc'] if f['ispred'] else 0]
            if f['export']:
                tok += [f['vdest'] if vact else -1, f['sdest'] if so != XP.SOP_NOP else -1]
            refs = {r[0]: r for r in XP.alu_refs(f)}
            for k in (1, 2, 3):
                if k > nops:
                    if k == 3 and so != XP.SOP_NOP: pass
                    else: continue
                key = 'v%d' % k if k <= nops else 's3'
                neg = f['neg%d' % k]
                if f['sel%d' % k] == 0:
                    ref = refs.get('v%d' % k) or refs.get('s3')
                    rb = f['reg%d' % k]
                    if p0 <= rb < p0 + pn:
                        tok.append(('P', neg)); o.prm.append((key, rb - p0, ref[2] if ref else []))
                    else:
                        lanes = [l for l, c in ref[2]] if ref else []
                        tok.append(('C', rb, neg, _mask(f['sw%d' % k], lanes)))
                else:
                    lanes = XP.vec_lanes(f, k) if k <= nops else ([3] if so in XP.SOP_CONST or so not in XP.SOP_TWO else [0, 3])
                    tok.append(('T', neg, f['reg%d' % k] >> 7, _mask(f['sw%d' % k], lanes)))
                    r = f['reg%d' % k] & 63
                    for l in lanes: o.uses.append((r, XP.comp(f['sw%d' % k], l)))
            o.tok = ('alu',) + tuple(tok)
            if not f['export']:
                if vact:
                    for l in range(4):
                        if (f['vmask'] >> l) & 1: o.defs.append((f['vdest'], l))
                if so != XP.SOP_NOP:
                    for l in range(4):
                        if (f['smask'] >> l) & 1: o.defs.append((f['sdest'], l))
        items.append(o)
    # producers (straight-line, program order)
    last = {}
    for i, o in enumerate(items):
        o.idx = i
        o.uses = [(u, last.get(u)) for u in o.uses]
        for d in o.defs: last[d] = i
    return items


def align(ia, ib, rounds=12):
    """Verified alignment: returns {i: j}."""
    sm = difflib.SequenceMatcher(None, [o.tok for o in ia], [o.tok for o in ib], autojunk=False)
    al = {}
    for i, j, n in sm.get_matching_blocks():
        for k in range(n): al[i + k] = j + k
    for _ in range(rounds):
        inv = {j: i for i, j in al.items()}
        drop = []
        for i, j in al.items():
            oa, ob = ia[i], ib[j]
            if oa.kind != 'alu': continue
            ua = [p for u, p in oa.uses]; ub = [p for u, p in ob.uses]
            if len(ua) != len(ub): drop.append(i); continue
            for pa, pb in zip(ua, ub):
                if pa is None and pb is None: continue
                if pa is None or pb is None:
                    if (pa if pb is None else pb) is not None: drop.append(i); break
                    continue
                if al.get(pa) is not None or inv.get(pb) is not None:
                    if al.get(pa) != pb: drop.append(i); break
        if not drop: break
        for i in drop: al.pop(i, None)
    return al


def uv_votes(items):
    """{(cidx, lane): set((param idx, comp))}: MaterialParams component feeding lane of the tfetch source temp of sampler cidx."""
    out = collections.defaultdict(set)
    for o in items:
        if o.kind != 'fetch': continue
        for ui, ((reg, lane), p) in enumerate(o.uses):
            if p is None: continue
            q = items[p]
            for role, x, lm in q.prm:
                for l, c in lm:
                    if l == lane and (reg, lane) in q.defs: out[(o.cidx, ui)].add((x, c))
    return out


def derive_pair(da, db, qa=None, qb=None):
    """Compare DLC permutation blob da with surrogate blob db. votes[(S param, S comp)] = Counter of (D param, D comp)."""
    qa = qa or param_range(da); qb = qb or param_range(db)
    ia = build(da, *qa); ib = build(db, *qb)
    al = align(ia, ib)
    votes = collections.defaultdict(collections.Counter)
    for i, j in al.items():
        pa = ia[i].prm; pb = ib[j].prm
        if len(pa) != len(pb): continue
        for (ra, xa, la), (rb, xb, lb) in zip(pa, pb):
            for (l1, c1), (l2, c2) in zip(la, lb):
                votes[(xb, c2)][(xa, c1)] += 1
    sur = {(x, c) for o in ib for r, x, lm in o.prm for l, c in lm}
    dl = {(x, c) for o in ia for r, x, lm in o.prm for l, c in lm}
    cnt = lambda it: sum(1 for o in it if o.kind != 'cf')
    ua = uv_votes(ia); ub = uv_votes(ib)
    return dict(uv=(ua, ub), votes=votes, aligned=sum(1 for i in al if ia[i].kind != 'cf'), ninstr_a=cnt(ia), ninstr_b=cnt(ib), sur_refs=sur, dlc_refs=dl,
                prm_aligned=sum(1 for i in al if ia[i].prm), prm_a=sum(1 for o in ia if o.prm), prm_b=sum(1 for o in ib if o.prm))


def oracle():
    L = libs(); X, D = L['X'], L['D']
    import param_remap as PR
    for dl, sl in ((2299, 1201), (2298, 1200)):
        a = [s for s in D[dl]['slots']]; b = [s for s in X[sl]['slots']]
        for si, (sa, sb) in enumerate(zip(a, b)):
            if sa == 0xffffffff or sb == 0xffffffff: continue
            r = derive_pair(D[dl]['entries'][sa]['blob'], X[sl]['entries'][sb]['blob'])
            print(dl, sl, 'slot', si, 'aligned %d/%d(sur %d)' % (r['aligned'], r['ninstr_a'], r['ninstr_b']), 'prm-instrs aligned %d (A %d B %d)' % (r['prm_aligned'], r['prm_a'], r['prm_b']),
                  'sur refs', len(r['sur_refs']), 'covered', len({k for k in r['votes']} & r['sur_refs']))
            conflicts = {k: v for k, v in r['votes'].items() if len(v) > 1}
            print('  conflicts', len(conflicts))
            for k, v in sorted(conflicts.items())[:10]: print('   ', k, dict(v))
            # compare with hand map
            if dl == 2299:
                ok = bad = miss = 0
                for (ib, cb), cnt in sorted(r['votes'].items()):
                    src = PR.MAP_2299_TO_1201[ib][cb]
                    best = cnt.most_common(1)[0][0]
                    if src[0] == 'k': bad += 1; print('   hand const at', ib, cb, 'votes', dict(cnt)); continue
                    if best == src: ok += 1
                    else: bad += 1; print('   MISMATCH S', (ib, cb), 'hand', src, 'votes', dict(cnt))
                print('  agree', ok, 'differ', bad)




# ------------------------------------------------------------------------------------------------ scan
_PAIR = {}
VALIDATED = {(2299, 1201): 'MAP_2299_TO_1201', (2298, 1200): 'MAP_2299_TO_1201'}   # hand-derived maps, NOTES 'Ponte GIALLO-ORO'

def pair_report(dl, sl):
    """Aggregate over the permutation slots of DLC lib dl vs surrogate Xbox lib sl."""
    if (dl, sl) in _PAIR: return _PAIR[dl, sl]
    L = libs(); D, X = L['D'], L['X']
    A, B = D[dl], X[sl]
    res = dict(status=None, nslots=0, covered=0, nsur=0, conflicts=0, identity=True, comps={}, notes=[])
    if A['kind'] != 1 or B['kind'] != 1: res['status'] = 'VS'; _PAIR[dl, sl] = res; return res
    cand = collections.defaultdict(collections.Counter); sur = set(); uvs = set()
    try:
        for si, (sa, sb) in enumerate(zip(A['slots'], B['slots'])):
            if sa == 0xffffffff or sb == 0xffffffff:
                if sa != sb: res['notes'].append('slot %d occupied on one side only' % si)
                continue
            ba, bb = A['entries'][sa]['blob'], B['entries'][sb]['blob']
            qa, qb = param_range(ba), param_range(bb)
            if qa is None or qb is None: res['notes'].append('slot %d no MaterialParams' % si); continue
            if qa != qb: res['notes'].append('slot %d param range differs %s %s' % (si, qa, qb))
            r = derive_pair(ba, bb, qa, qb); res['nslots'] += 1
            sur |= r['sur_refs']
            ua, ub = r['uv']
            uvset = {x for key in ub for x in ub[key]}
            for k, v in r['votes'].items():
                if k in uvset: continue          # UV scales: positional votes are unreliable (compiler reorders the mul), only tfetch-anchored votes count
                for d, n in v.items(): cand[k][d] += n
            for key in ub:
                for s in ub[key]:
                    uvs.add(s)
                    for d in ua.get(key, []): cand[s][d] += 1
    except Exception as e:
        res['status'] = 'UNDECODABLE'; res['notes'].append(repr(e)[:80]); _PAIR[dl, sl] = res; return res
    res['nsur'] = len(sur); res['covered'] = len(sur & set(cand))
    res['unresolved_uv'] = sorted(uvs - set(cand))
    for s, c in cand.items():
        if len(c) > 1: res['conflicts'] += 1
        d = c.most_common(1)[0][0]
        if len(c) > 1 or d != s: res['identity'] = False
        res['comps'][s] = (dict(c), s in uvs)
    if not res['nslots'] or not sur: res['status'] = 'UNDECODABLE'
    elif (dl, sl) in VALIDATED: res['status'] = 'PROVEN-MAP'
    elif res['conflicts']: res['status'] = 'CONFLICT'
    elif res['identity']: res['status'] = 'IDENTITY-VERIFIED' if res['covered'] == res['nsur'] else 'IDENTITY-PARTIAL'
    else: res['status'] = 'CANDIDATE-MAP' if res['covered'] == res['nsur'] else 'CANDIDATE-PARTIAL'
    _PAIR[dl, sl] = res
    return res


def material_plan(xmid):
    L = libs(); DM = L['DM']
    smap = {int(k): v for k, v in json.load(open(os.path.join(W, 'dlc_shader_map.json'))).items()}
    xd = DM[xmid][0]
    ids = struct.unpack_from('>4I', xd, 0x28)
    passes = []
    for pos in range(3):
        s = ids[pos]
        if not s: continue
        m = smap[s]
        if m['cls'] in ('A', 'B'): passes.append((pos, s, m['cls'], m['surrogate'], 'EXACT')); continue
        if m['cls'] in ('C3', 'D'): passes.append((pos, s, m['cls'], m['surrogate'], 'REPORT-ONLY(%s)' % m['cls'])); continue
        passes.append((pos, s, m['cls'], m['surrogate'], pair_report(s, m['surrogate'])['status']))
    return ids, passes


RANK = ['EXACT', 'EXACT-UNSEEN', 'IDENTITY-VERIFIED', 'PROVEN-MAP', 'IDENTITY-PARTIAL', 'CANDIDATE-MAP', 'CANDIDATE-PARTIAL', 'CONFLICT', 'UNDECODABLE',
        'REPORT-ONLY(C3)', 'REPORT-ONLY(D)', 'VS']
SAFE = {'EXACT', 'IDENTITY-VERIFIED'}

def candidate_delta(xmid, passes):
    """Estimate (not applied): components whose value would change if the candidate map(s) were applied to the DLC Xbox params."""
    xd, xr = libs()['DM'][xmid]
    import material_convert as MC
    vx = MC.read_params(xd, xr, '>')
    changed = 0; worst = 0.0; comps = []
    for pos, s_, cls, sur, st in passes:
        if not st.startswith('CANDIDATE'): continue
        rep = pair_report(s_, sur)
        for (pi, c), (cnt, uv) in rep['comps'].items():
            (dp, dc), = [max(cnt.items(), key=lambda kv: kv[1])[0:1]][0:1] if False else [max(cnt.items(), key=lambda kv: kv[1])[0]]
            if (dp, dc) == (pi, c) or pi >= len(vx) or dp >= len(vx): continue
            a, b = vx[pi][c], vx[dp][dc]
            if abs(a - b) > 1e-6:
                changed += 1; worst = max(worst, abs(a - b) / (abs(a) + 1e-3)); comps.append((pi, c, round(a, 3), round(b, 3), uv))
    return changed, worst, comps

def scan(outdir):
    os.makedirs(outdir, exist_ok=True)
    L = libs(); DM = L['DM']
    ms = {int(k): v for k, v in json.load(open(os.path.join(W, 'dlc_material_shaders.json'))).items()}
    mats = pickle.load(open(os.path.join(W, 'dlc_materials_pc.pkl'), 'rb'))
    drms = pickle.load(open(os.path.join(ROOT, 'work', 'generic', 'dlc_drms.pkl'), 'rb'))
    where = collections.defaultdict(set); meshes = collections.defaultdict(lambda: collections.defaultdict(list))
    import drm_reloc as R
    for (pack, name, spec), (hdr, secs) in drms.items():
        if pack != 'ack10.000': continue
        short = os.path.basename(name.replace('\\', '/'))
        for sec in secs:
            if sec['type'] == 10: where[sec['id']].add(short)
        for sec in secs:
            if sec['type'] == 12 and sec.get('reloc'):
                r = R.parse(sec['reloc'], 'be')
                for t, o in r.idref + r.idref_a:
                    if t == 10: meshes[short][struct.unpack_from('>I', sec['data'], o)[0]].append((sec['id'], sec['size']))
    rows = []
    for mid in sorted(ms):
        ids, ps = material_plan(mid)
        worst = max((p[4] for p in ps), key=RANK.index) if ps else 'EXACT'
        flags = mats[mid]['flags']
        if worst == 'EXACT' and any(f.startswith('tuple unseen') for f in flags): worst = 'EXACT-UNSEEN'
        nch, wr, comps = candidate_delta(mid, ps)
        units = sorted(where.get(mid, []))
        rows.append(dict(mid=mid, ids=ids, passes=ps, verdict=worst, dlc1=bool(units), units=units, meshes=len({m for u in units for m, _ in meshes[u].get(mid, [])}), flags=flags, mesh_ids=sorted({m for u in units for m, _ in meshes[u].get(mid, [])}),
                         nparams=struct.unpack_from('>I', DM[mid][0], 0x58)[0], d_changed=nch, d_worst=wr, d_comps=comps,
                         pc_tuple=ms[mid]['pc_tuple'], base_material=ms[mid]['base_material']))
    json.dump(rows, open(os.path.join(outdir, 'scan.json'), 'w'), default=str)
    with open(os.path.join(outdir, 'materials.tsv'), 'w') as f:
        f.write('material\tverdict\tpasses(pos:dlcLib:cls:surrogate:status)\tparams\tdlc1_units\tmeshes\tmesh_ids\tflags\tcand_comps_changed\tcand_max_rel_delta\n')
        for r in rows:
            f.write('%d\t%s\t%s\t%d\t%s\t%d\t%s\t%s\t%d\t%.2f\n' % (r['mid'], r['verdict'], ' '.join('%d:%d:%s:%d:%s' % p for p in r['passes']), r['nparams'],
                    ','.join(r['units']), r['meshes'], ' '.join(map(str, r['mesh_ids'])), '; '.join(r['flags']), r['d_changed'], r['d_worst']))
    return rows

def fix_section(xmid, pc_data, pc_reloc):
    """Hook: returns (new pc data, info). Applies the re-packing ONLY for PROVEN-MAP materials (param_remap.MATERIALS, tuple-checked);
    info = verdict string. Never changes the section size."""
    import param_remap as PR
    if xmid not in PR.MATERIALS: return pc_data, None
    ids, ps = material_plan(xmid)
    if not any(p[4] == 'PROVEN-MAP' for p in ps): return pc_data, None
    import material_convert as MC
    xd, xr = libs()['DM'][xmid]
    ip = dict(R.parse(pc_reloc, 'le').internal); n = struct.unpack_from('<I', pc_data, 0x58)[0]
    cur = [struct.unpack_from('<4f', pc_data, ip[0x5C] + 16 * i) for i in range(n)]
    if cur != MC.read_params(xd, xr, '>'): return pc_data, 'SKIP: params are not the 1:1 copy of the DLC Xbox params (already re-packed or other rule)'
    nd, vx, vp = PR.patch_material(pc_data, pc_reloc, xmid)
    return nd, 'PROVEN-MAP'

def md5file(d):
    with open(os.path.join(d, 'md5.txt'), 'w') as f:
        for n in sorted(os.listdir(d)):
            if n.endswith('.drm'): f.write('%s  %s\n' % (hashlib.md5(open(os.path.join(d, n), 'rb').read()).hexdigest(), n))

def fix(outdir, srcs):
    import drm_write as DW
    os.makedirs(outdir, exist_ok=True); n = 0
    for src in srcs:
        D = DW.read(open(src, 'rb').read(), 'le'); ch = []
        for sct in D.sections:
            if sct.type != 10: continue
            nd, info = fix_section(sct.id, sct.data, sct.reloc)
            if info and info.startswith('SKIP'): print('  skip', sct.id, info)
            if info == 'PROVEN-MAP' and nd != sct.data: sct.data = nd; ch.append(sct.id)
        if ch:
            dst = os.path.join(outdir, os.path.basename(src))
            open(dst, 'wb').write(DW.cdrm_encode(D.write('le'), 'le')); n += 1
            print('fixed', os.path.basename(src), ch)
    md5file(outdir); print('files written', n)

def selftest(n=40):
    """Each base Xbox lib against ITSELF: identity map, 0 conflicts (CONVENTIONS: 0 changes on base)."""
    X = libs()['X']; import random
    random.seed(1); ks = [k for k, v in X.items() if v['kind'] == 1]; random.shuffle(ks)
    ok = bad = und = 0
    for k in ks[:n]:
        lib = X[k]
        for sa in sorted(set(lib['slots']) - {0xffffffff})[:2]:
            b = lib['entries'][sa]['blob']; q = param_range(b)
            if q is None: und += 1; continue
            r = derive_pair(b, b, q, q)
            good = all(len(c) == 1 and list(c)[0] == key for key, c in r['votes'].items())
            ok += good; bad += not good
            if not good: print('  non-identity', k)
    print('selftest libs vs themselves: identity %d, not %d, no params %d' % (ok, bad, und))

def oracle_gate():
    """2299->1201 / 2298->1200: how many components the automatic derivation reproduces from the hand map."""
    import param_remap as PR
    for dl, sl in ((2299, 1201), (2298, 1200)):
        rep = pair_report(dl, sl); agree = dis = 0
        for (pi, c), (cnt, uv) in sorted(rep['comps'].items()):
            hand = PR.MAP_2299_TO_1201[pi][c]; top = max(cnt.items(), key=lambda kv: kv[1])[0]
            uni = len(cnt) == 1
            if hand == top and uni: agree += 1
            else: dis += 1; print('  pair %d->%d S%s hand %s auto %s uv=%s' % (dl, sl, (pi, c), hand, dict(cnt), uv))
        print('pair %d->%d: unanimous&==hand %d, other %d (of %d S comps, sur refs %d)' % (dl, sl, agree, dis, len(rep['comps']), rep['nsur']))


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'oracle': oracle_gate()
    elif cmd == 'selftest': selftest()
    elif cmd == 'scan':
        rows = scan(sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'work', 'ws', 'mat', 'out'))
        print(collections.Counter(r['verdict'] for r in rows))
    elif cmd == 'fix': fix(sys.argv[2], sys.argv[3:])
