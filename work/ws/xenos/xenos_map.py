"""MaterialParams map from the SYMBOLIC translation (xenos_xlat.IRBuilder), as an alternative to tools/param_auto.py's instruction alignment.

Idea.  D (DLC lib, Xenos) and S (surrogate base lib, Xenos; its PC build is what the engine runs) come from the same shader graph.
Both are evaluated symbolically (register file -> expression DAG over: MaterialParams components P(i,c), other named CTAB constants,
interpolators, texture fetches, literals).  The two DAGs are canonicalised (mad/dp expanded, add/mul n-ary and flattened, neg folded into
mul by -1) and UNIFIED from the export roots (oC0.xyzw, ...): structurally equal subtrees pair their P leaves.  A pair (S param (i,c) <- D
param (j,d)) is a vote;  S literal vs D param, D literal vs S param give ('k', v) votes;  texture fetch nodes pair sampler registers.
Commutative n-ary children with identical shape (typically two P leaves) are disambiguated in a second phase with the map established by
the unambiguous first phase (permutation scoring); ties stay AMBIGUOUS and are reported, never guessed.

usage:  tools/venv/bin/python -I work/ws/xenos/xenos_map.py oracle        (2299->1201 and 2298->1200 against the hand map of tools/param_remap.py)
"""
import sys, os, collections, itertools
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'tools'))
import xenos_xlat as X
sys.setrecursionlimit(100000)

COMM = {'add', 'mul'}
COMM2 = {'max', 'min', 'seq', 'sne'}


LEVELS = (1, 2, 3, 5, 8, 99)


class Shapes:
    """Canonical depth-limited shape ids of an IR (P leaves, literal values and sampler registers are wildcards; subtrees below `depth`
    collapse to their kind).  depth 99 = whole tree."""
    def __init__(self, ir, tab=None):
        self.ir = ir; self.memo = {}; self.tab = {} if tab is None else tab

    def sid(self, key):
        i = self.tab.get(key)
        if i is None: i = self.tab[key] = len(self.tab)
        return i

    def of(self, n, depth=99):
        k0 = (n, depth)
        m = self.memo.get(k0)
        if m is not None: return m
        nd = self.ir.nodes[n]; k = nd[0]
        if k == 'k': key = ('k',)
        elif k == 'P': key = ('P',)
        elif k == 'U': key = ('U',)
        elif k == 'B': key = ('B', nd[1])
        elif k == 'C': key = ('C', nd[1], nd[2], nd[3])
        elif k == 'V': key = ('V', nd[1], nd[2], nd[3])
        elif depth <= 0: key = ('~', k) if k not in ('T', 'TC') else ('~', k, nd[2] if k == 'TC' else nd[2])
        elif k == 'T': key = ('T', nd[2], nd[3]) + tuple(self.of(c, depth - 1) for c in nd[4:])
        elif k == 'TC': key = ('TC', self.of(nd[1], depth - 1), nd[2])
        elif k in COMM or k in COMM2: key = (k,) + tuple(sorted(self.of(c, depth - 1) for c in nd[1:]))
        else: key = (k,) + tuple(self.of(c, depth - 1) if isinstance(c, int) and not isinstance(c, bool) else c for c in nd[1:])
        m = self.memo[k0] = self.sid(key)
        return m


class Unifier:
    def __init__(self, irD, irS):
        self.D, self.S = irD, irS
        tab = {}
        self.shD, self.shS = Shapes(irD, tab), Shapes(irS, tab)
        self.votes = collections.defaultdict(collections.Counter)      # (S idx, comp) -> Counter of (D idx, comp) | ('k', v)   (exact context)
        self.wvotes = collections.defaultdict(collections.Counter)     # same, obtained below a structural divergence (approximate pairing)
        self.svotes = collections.defaultdict(collections.Counter)     # S sampler reg -> Counter D sampler reg
        self.done = {}
        self.fail = collections.Counter(); self.ambig = []; self.folded = collections.Counter(); self.kdiff = 0
        self.deferred = []; self.dry_depth = 0; self.weak = False
        self.established = {}
        self.ratios = collections.defaultdict(collections.Counter)    # (S comp) -> Counter((D comp, kD/kS)) from mul nodes with one P factor each

    def uni(self, a, b, votes=None, svotes=None, phase=1, memo=True):
        votes = self.votes if votes is None else votes
        svotes = self.svotes if svotes is None else svotes
        if memo is True: tab = self.done
        elif memo is False or memo is None: tab = {}
        else: tab = memo
        key = (a, b, self.weak)
        r = tab.get(key)
        if r is not None: return r
        tab[key] = True
        r = self._uni(a, b, votes, svotes, phase, tab if memo is not True else True)
        tab[key] = r
        return r

    def _uni(self, a, b, votes, svotes, phase, memo):
        nd, ns = self.D.nodes[a], self.S.nodes[b]
        ka, kb = nd[0], ns[0]
        if self.weak and votes is self.votes: votes = self.wvotes
        if ka == 'P' and kb == 'P':
            votes[(ns[1], ns[2])][(nd[1], nd[2])] += 1; return True
        if ka == 'k' and kb == 'P':
            votes[(ns[1], ns[2])][('k', nd[1])] += 1; return True
        if ka == 'P' and kb == 'k':
            self.folded[(nd[1], nd[2], ns[1])] += 1; return True
        if ka == 'k' and kb == 'k':
            if nd[1] != ns[1]: self.kdiff += 1
            return True
        if ka == 'U' and kb == 'U': return True
        if ka != kb:
            self.fail[(ka, kb)] += 1; return False
        if ka in ('C', 'V', 'B'):
            return nd[1:] == ns[1:]
        if ka == 'T':
            if nd[2] != ns[2] or nd[3] != ns[3] or len(nd) != len(ns): self.fail[('T', 'T-flags')] += 1; return False
            ok = True
            for c1, c2 in zip(nd[4:], ns[4:]): ok &= self.uni(c1, c2, votes, svotes, phase, memo)
            if not self.weak: svotes[ns[1]][nd[1]] += 1
            return ok
        if ka == 'TC':
            return nd[2] == ns[2] and self.uni(nd[1], ns[1], votes, svotes, phase, memo)
        if len(nd) != len(ns):
            self.fail[(ka, 'arity')] += 1; return False
        if ka == 'mul' and not self.weak and self.dry_depth == 0:
            pD = [c for c in nd[1:] if self.D.nodes[c][0] == 'P']; pS = [c for c in ns[1:] if self.S.nodes[c][0] == 'P']
            if len(pD) == 1 and len(pS) == 1:
                kD = next((self.D.nodes[c][1] for c in nd[1:] if self.D.nodes[c][0] == 'k'), 1.0)
                kS = next((self.S.nodes[c][1] for c in ns[1:] if self.S.nodes[c][0] == 'k'), 1.0)
                if kS != 0:
                    a1, b1 = self.D.nodes[pD[0]], self.S.nodes[pS[0]]
                    self.ratios[(b1[1], b1[2])][((a1[1], a1[2]), round(kD / kS, 4))] += 1
        if ka in COMM or ka in COMM2:
            return self.nary(nd[1:], ns[1:], votes, svotes, phase, memo)
        ok = True
        for c1, c2 in zip(nd[1:], ns[1:]):
            if isinstance(c1, int) and isinstance(c2, int) and not isinstance(c1, bool):
                ok &= self.uni(c1, c2, votes, svotes, phase, memo)
            elif c1 != c2: ok = False
        return ok

    def score(self, c, d):
        s = 0
        for lv in LEVELS:
            if self.shD.of(c, lv) == self.shS.of(d, lv): s = lv
            else: break
        return s

    def nary(self, ca, cb, votes, svotes, phase, memo):
        ca = list(dict.fromkeys(ca)); cb = list(dict.fromkeys(cb))
        uD = set(ca); uS = set(cb)
        sc = {(c, d): self.score(c, d) for c in ca for d in cb}
        ok = len(ca) == len(cb)
        matched = []
        progress = True
        while progress and uD and uS:
            progress = False
            best = {}
            for c in uD:
                m = max((sc[c, d] for d in uS), default=-1)
                best[c] = (m, [d for d in uS if sc[c, d] == m])
            bestS = {}
            for d in uS:
                m = max((sc[c, d] for c in uD), default=-1)
                bestS[d] = (m, [c for c in uD if sc[c, d] == m])
            for c in sorted(uD, key=lambda x: -best[x][0]):
                m, ds = best[c]
                if m < 1 or len(ds) != 1: continue
                d = ds[0]
                if d not in uS or c not in uD: continue
                if bestS[d][0] == m and bestS[d][1] == [c]:
                    matched.append((c, d, m)); uD.discard(c); uS.discard(d); progress = True
        for c, d, m in matched:
            old = self.weak
            if m < 99: self.weak = True; ok = False
            self.uni(c, d, votes, svotes, phase, memo)
            self.weak = old
        if uD or uS:
            ok = False
            if phase == 1 and memo is True and uD and uS:
                self.deferred.append((sorted(uD), sorted(uS), self.weak))
            elif uD and uS:
                self.resolve(sorted(uD), sorted(uS), votes, svotes, memo, self.weak)
        return ok

    def resolve(self, la, lb, votes, svotes, memo, weak=True):
        est = self.established
        if self.dry_depth > 0 or min(len(la), len(lb)) == 0: return False
        small, big, swap = (la, lb, False) if len(la) <= len(lb) else (lb, la, True)
        if len(big) > 7: self.ambig.append((la, lb, 'too many')); return False
        best = None; tie = False
        for perm in itertools.permutations(range(len(big)), len(small)):
            v = collections.defaultdict(collections.Counter); sv = collections.defaultdict(collections.Counter)
            self.dry_depth += 1; tab = {}; okc = 0
            oldw = self.weak; self.weak = False
            for i, j in enumerate(perm):
                c, d = (small[i], big[j]) if not swap else (big[j], small[i])
                okc += bool(self.uni(c, d, v, sv, 2, tab))
            self.weak = oldw
            self.dry_depth -= 1
            score = 0
            for sk, cnt in v.items():
                for dk, n in cnt.items():
                    e = est.get(sk)
                    if e is None: continue
                    score += n if e == dk else -n
            cand = (okc, score)
            if best is None or cand > best[0]: best = (cand, perm); tie = False
            elif cand == best[0]: tie = True
        if best is None or tie or best[0][0] == 0:
            self.ambig.append((la, lb, 'tie' if tie else 'no-match')); return False
        old = self.weak; self.weak = weak
        for i, j in enumerate(best[1]):
            c, d = (small[i], big[j]) if not swap else (big[j], small[i])
            self.uni(c, d, votes, svotes, 2, True)
        self.weak = old
        return True

    def run(self, rootsD, rootsS):
        roots = sorted(set(rootsD) & set(rootsS))
        res = {}
        for rk in roots: res[rk] = self.uni(rootsD[rk], rootsS[rk])
        self.established = {}
        for sk, cnt in self.votes.items():
            if len(cnt) == 1: self.established[sk] = next(iter(cnt))
        pending = self.deferred; self.deferred = []
        for la, lb, w in pending:
            self.resolve(la, lb, self.votes, self.svotes, True, w)
        self.roots_ok = res
        self.roots_missing = (len(set(rootsD) - set(rootsS)), len(set(rootsS) - set(rootsD)))
        return res


def s_leaves(ir, roots):
    """set of (param idx, comp) referenced by the S expression DAGs of the roots."""
    seen = set(); out = set(); st = list(roots.values())
    while st:
        n = st.pop()
        if n in seen: continue
        seen.add(n); nd = ir.nodes[n]
        if nd[0] == 'P': out.add((nd[1], nd[2]))
        for c in nd[1:]:
            if isinstance(c, int) and not isinstance(c, bool) and nd[0] not in ('P', 'C', 'V', 'U', 'k') and (nd[0] != 'T' or True):
                if nd[0] in ('T',) and c is nd[1]: continue
                st.append(c)
    return out


def build_ir(blob):
    sh = X.parse(blob)
    b = X.IRBuilder(sh)
    roots = b.run()
    return sh, b, roots


def map_pair(blobD, blobS):
    """One permutation pair.  Returns dict(votes, svotes, s_refs, roots_ok, ...)."""
    shD, bD, rD = build_ir(blobD); shS, bS, rS = build_ir(blobS)
    U = Unifier(bD.ir, bS.ir)
    U.run(rD, rS)
    refs = s_leaves(bS.ir, rS)
    return dict(U=U, s_refs=refs, nroots=(len(rD), len(rS)), roots_ok=U.roots_ok, notes=(dict(bD.notes), dict(bS.notes)), ambig=len(U.ambig), shD=shD, shS=shS)


def summarize(r):
    """classification of a pair result: for each S param component referenced: unanimous / conflict / uncovered."""
    votes = r['U'].votes
    una = {}; conf = {}; unc = []
    for s in sorted(r['s_refs']):
        c = votes.get(s)
        if not c: unc.append(s)
        elif len(c) == 1: una[s] = next(iter(c))
        else: conf[s] = dict(c)
    return una, conf, unc


def oracle():
    import pickle, param_remap as PR
    L = X.load_libs(); D, Xl = L['D'], L['X']
    for dl, sl in ((2299, 1201), (2298, 1200)):
        agree = dis = nov = 0; tot_unc = 0; tot_conf = 0; roots = 0; rok = 0; amb = 0
        allvotes = collections.defaultdict(collections.Counter); weakv = collections.defaultdict(collections.Counter)
        refs_all = set()
        for si, (sa, sb) in enumerate(zip(D[dl]['slots'], Xl[sl]['slots'])):
            if sa == 0xffffffff or sb == 0xffffffff: continue
            r = map_pair(D[dl]['entries'][sa]['blob'], Xl[sl]['entries'][sb]['blob'])
            roots += len(r['roots_ok']); rok += sum(r['roots_ok'].values()); amb += r['ambig']
            for s, c in r['U'].votes.items():
                for d, n in c.items(): allvotes[s][d] += n
            for s, c in r['U'].wvotes.items():
                for d, n in c.items(): allvotes[s][d] += n; weakv[s][d] += n
            refs_all |= r['s_refs']
        print('pair %d->%d: slots ok; roots unified %d/%d, ambiguous groups %d' % (dl, sl, rok, roots, amb))
        una = {s: next(iter(c)) for s, c in allvotes.items() if len(c) == 1}
        for s in sorted(refs_all):
            hand = PR.MAP_2299_TO_1201[s[0]][s[1]]
            c = allvotes.get(s)
            if not c: nov += 1; continue
            if len(c) > 1:
                dis += 1; print('   CONFLICT S%s hand %s votes %s' % (s, hand, dict(c))); continue
            got = next(iter(c))
            if got == hand or (hand[0] == 'k' and got[0] == 'k' and abs(hand[1] - got[1]) < 1e-3): agree += 1
            else: dis += 1; print('   DIFF S%s hand %s auto %s' % (s, hand, got))
        print('   S param components referenced: %d  -> unanimous & equal to hand map %d, differ/conflict %d, no vote %d' % (len(refs_all), agree, dis, nov))


if __name__ == '__main__':
    if sys.argv[1] == 'oracle': oracle()
