"""(2)+(3) Case studies: translate the PS libs and compute the MaterialParams map D->S with xenos_map (symbolic unification), reporting
per S component: strong votes (exact structural context), weak votes (below a divergence), conflicts, multiplier ratios, sampler map, and
what tools/param_auto.py (instruction alignment, with and without the microcode-extraction fix) says for the same pair.
usage: tools/venv/bin/python -I work/ws/xenos/case_study.py DLIB SLIB [tag]"""
import sys, os, collections, json
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'tools'))
import xenos_xlat as X, xenos_map as M

def run(dl, sl, tag=None, write=True):
    L = X.load_libs(); D, Xl = L['D'], L['X']
    lib_d = D.get(dl) or Xl[dl]; lib_s = Xl[sl]
    out = []
    P = lambda *a: out.append(' '.join(str(x) for x in a))
    P('# case %s: DLC lib %d (%s) -> surrogate Xbox lib %d' % (tag, dl, 'D' if dl in D else 'X', sl))
    agg_s = collections.defaultdict(collections.Counter); agg_w = collections.defaultdict(collections.Counter)
    ratios = collections.defaultdict(collections.Counter); sv = collections.defaultdict(collections.Counter)
    refs = set(); nroots = rok = 0; npairs = 0; fails = collections.Counter(); nodes = 0; ambig = 0; notes = collections.Counter()
    dparams = set()
    first = True
    for si, (sa, sb) in enumerate(zip(lib_d['slots'], lib_s['slots'])):
        if sa == 0xffffffff or sb == 0xffffffff:
            if sa != sb: P('slot', si, 'occupied on one side only')
            continue
        bd, bs = lib_d['entries'][sa]['blob'], lib_s['entries'][sb]['blob']
        if first and write:
            for nm, b, lid in (('D', bd, dl), ('S', bs, sl)):
                sh = X.parse(b); T = X.text(sh, 'pretty')
                head = ['// %s lib %d slot %d  %s  ctab=%s' % (nm, lid, si, 'PS' if sh.is_ps else 'VS', [(c['name'][:40], c['set'], c['reg'], c['count']) for c in sh.ctab]),
                        '// interpolators %s  outputs %s  inline defs %s' % (sh.interp, sh.outputs, {k: tuple(round(x, 4) for x in v) for k, v in sh.defs.items()}),
                        '// features %s' % dict(X.summary(sh))]
                cu = []
                for reg in sorted(T.uses):
                    e = sh.f4.get(reg)
                    cu.append('c%d=%s %s' % (reg, ('%s[%d]' % (e[0]['name'], e[1]) if e else ('def' if reg in sh.defs else '?')), ''.join('xyzw'[c] for c in sorted(T.uses[reg]))))
                head.append('// float constants read (register=name[index] components): ' + '; '.join(cu))
                head.append('// samplers fetched (register, name, dim) x count: ' + '; '.join('s%d %s %s x%d' % (k[0], k[1][:48], k[2], n) for k, n in sorted(T.samp_uses.items())))
                head.append('// unsupported/dropped: %s' % dict(T.unsup))
                open(os.path.join(HERE, 'out', 'xlat_%s_%s_%d.txt' % (tag, nm, lid)), 'w').write('\n'.join(head + T.lines) + '\n')
            first = False
        try:
            r = M.map_pair(bd, bs)
        except Exception as e:
            P('slot', si, 'EXCEPTION', repr(e)[:100]); continue
        npairs += 1
        U = r['U']
        nroots += len(r['roots_ok']); rok += sum(r['roots_ok'].values()); ambig += len(U.ambig); nodes += len(U.D.nodes) + len(U.S.nodes)
        for k, v in U.fail.items(): fails[k] += v
        for k, v in r['notes'][0].items(): notes[k] += v
        for s_, c in U.votes.items():
            for d, n in c.items(): agg_s[s_][d] += n
        for s_, c in U.wvotes.items():
            for d, n in c.items(): agg_w[s_][d] += n
        for s_, c in U.ratios.items():
            for d, n in c.items(): ratios[s_][d] += n
        for s_, c in U.svotes.items():
            for d, n in c.items(): sv[s_][d] += n
        refs |= r['s_refs']
        # D params referenced
        for n_ in U.D.nodes:
            if n_[0] == 'P': dparams.add((n_[1], n_[2]))
    P('permutation pairs analysed: %d ; roots unified exactly %d/%d ; ambiguous groups %d ; IR nodes %d' % (npairs, rok, nroots, ambig, nodes))
    P('structural failures (kind pairs): %s' % dict(fails.most_common(6)))
    P('D control-flow/special notes (summed over slots): %s' % dict(notes))
    P('S param components referenced by the S expressions: %d ; D param components referenced: %d' % (len(refs), len(dparams)))
    cls = collections.Counter(); table = []
    for s_ in sorted(refs):
        st = agg_s.get(s_, {}); wk = agg_w.get(s_, {})
        allv = collections.Counter(st) + collections.Counter(wk)
        if not allv: c = 'NO-VOTE'; best = None
        elif len(st) == 1 and len(allv) == 1: c = 'UNANIMOUS-STRONG'; best = next(iter(st))
        elif len(allv) == 1: c = 'UNANIMOUS-WEAK'; best = next(iter(allv))
        elif st and len({d for d in st}) == 1 and max(allv.values()) == st[next(iter(st))]: c = 'STRONG-OVER-WEAK'; best = next(iter(st))
        else: c = 'CONFLICT'; best = allv.most_common(1)[0][0]
        rt = ratios.get(s_); rts = ''
        if rt and best and best[0] != 'k':
            rr = [(d, n) for d, n in rt.items() if d[0] == best]
            if rr: rts = ' ratio(D/S const)=%s' % sorted(set(d[1] for d, n in rr))
        cls[c] += 1
        table.append((s_, c, best, dict(allv) if c in ('CONFLICT', 'STRONG-OVER-WEAK') else '', rts))
    P('classification of S components:', dict(cls))
    for s_, c, best, extra, rts in table:
        P('  S c%d.%s  %-17s <- %s %s%s' % (100 + s_[0], 'xyzw'[s_[1]], c, ('D c%d.%s' % (100 + best[0][0], 'xyzw'[best[0][1]]) if best and best[0] != 'k' and isinstance(best[0], tuple) else (('D c%d.%s' % (100 + best[0], 'xyzw'[best[1]])) if best and best[0] != 'k' else ('const %g' % best[1] if best else '-'))), extra, rts))
    P('sampler register map S<-D (votes):', {s_: dict(c) for s_, c in sorted(sv.items())})
    if write: open(os.path.join(HERE, 'out', 'case_%s.txt' % tag), 'w').write('\n'.join(out) + '\n')
    return out, table, cls

if __name__ == '__main__':
    dl, sl = int(sys.argv[1]), int(sys.argv[2]); tag = sys.argv[3] if len(sys.argv) > 3 else '%d_%d' % (dl, sl)
    out, _, _ = run(dl, sl, tag)
    print('\n'.join(out))
