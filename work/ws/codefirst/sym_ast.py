"""TASK 1 (giro 3): AST/dataflow SIMBOLICO del blocco luci (Xbox e PC) con normalizzazione algebrica, e firma di RUOLO di ogni lane MaterialParams.
Nodo = tupla interna (op, figli...). Normalizzazioni: mov trasparente; mad->add(mul); sub->add(neg); add/mul appiattiti e ordinati (commutativi/associativi);
segno estratto dai mul; neg(add)->add di termini negati; exp2(mul(.., log2 b))->pow(b, ..); max(x,x)->x; sat/shift espliciti.
Firma di ruolo di una lane = insieme delle catene ASCENDENTI (fino a profondita' D) dalla foglia verso le uscite: (op, ruolo della posizione) senza nomi di registro."""
import sys, collections; sys.path.insert(0, '/path/to/trudlcport/work/ws/shader4'); sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
import sm3asm
from f9_transplant import *
from f9_common import lanes as _lanes

RT = sm3asm

class Dag:
    def __init__(self):
        self.tab = {}; self.nodes = []
    def mk(self, *t):
        if t not in self.tab: self.tab[t] = len(self.nodes); self.nodes.append(t)
        return self.tab[t]
    def leaf(self, kind, *a): return self.mk('L', kind, *a)
    def neg(self, x):
        n = self.nodes[x]
        if n[0] == 'neg': return n[1]
        if n[0] == 'mul':
            fs = list(n[1:]); return self.mulf([self.neg(fs[0])] + fs[1:]) if False else self.mk('neg', x)
        if n[0] == 'add': return self.addf([self.neg(t) for t in n[1:]])
        return self.mk('neg', x)
    def addf(self, ts):
        fl = []
        for t in ts:
            n = self.nodes[t]
            if n[0] == 'add': fl += list(n[1:])
            else: fl.append(t)
        # cancellazione t + (-t)
        res = list(fl)
        for t in list(res):
            if t in res and self.neg(t) in res and t != self.neg(t):
                res.remove(t); res.remove(self.neg(t))
        if not res: return self.leaf('lit', 0.0)
        if len(res) == 1: return res[0]
        return self.mk('add', *sorted(res))
    def mulf(self, fs):
        fl = []; sgn = 0
        for f in fs:
            n = self.nodes[f]
            while n[0] == 'neg': sgn ^= 1; f = n[1]; n = self.nodes[f]
            if n[0] == 'mul': fl += list(n[1:])
            else: fl.append(f)
        r = self.mk('mul', *sorted(fl)) if len(fl) > 1 else fl[0]
        return self.mk('neg', r) if sgn else r
    def un(self, op, x): return self.mk(op, x)

def build(prog, a, b, mp_lo=100, mp_hi=116):
    """esegue simbolicamente body[a:b]; ritorna (dag, env (temp,reg,comp)->nodo, lista istruzioni con nodo prodotto)."""
    D = Dag(); env = {}; st = stypes(prog); log = []
    def reg_val(o, comp):
        if o.rtype == RT.RT_TEMP:
            return env.get((o.num, comp)) or D.leaf('in', o.num, comp)
        if o.rtype in (RT.RT_CONST, RT.RT_CONST2):
            if mp_lo <= o.num < mp_hi and o.rtype == RT.RT_CONST: return D.leaf('mp', o.num, comp)
            return D.leaf('k', o.rtype, o.num, comp)
        if o.rtype == RT.RT_CONSTBOOL: return D.leaf('bool', o.num)
        return D.leaf('o%d' % o.rtype, o.num, comp)
    def src(o, k):
        c = (o.swz >> (2 * k)) & 3; v = reg_val(o, c); m = o.smod
        if m == 0: return v
        if m == 1: return D.neg(v)
        if m == 6: return D.addf([D.leaf('lit', 1.0), D.neg(v)])
        if m == 7: return D.mulf([v, D.leaf('lit', 2.0)])
        if m == 8: return D.neg(D.mulf([v, D.leaf('lit', 2.0)]))
        if m == 11: return D.mk('abs', v)
        if m == 12: return D.neg(D.mk('abs', v))
        return D.mk('smod%d' % m, v)
    for idx, i in enumerate(body(prog)[a:b]):
        op = i.op
        if op in ('if', 'ifc', 'else', 'endif', 'dcl', 'def', 'defi', 'defb', 'nop', 'texkill', 'setp') or not i.ops or not i.ops[0].isdst: continue
        d = i.ops[0]; ss = i.ops[1:-1] if i.pred else i.ops[1:]
        if d.rtype != RT.RT_TEMP: continue
        out = {}
        for k in range(4):
            if not d.wm >> k & 1: continue
            S = lambda n_, kk=k: src(ss[n_], kk)
            if op == 'mov': v = S(0)
            elif op == 'add': v = D.addf([S(0), S(1)])
            elif op == 'sub': v = D.addf([S(0), D.neg(S(1))])
            elif op == 'mul': v = D.mulf([S(0), S(1)])
            elif op == 'mad': v = D.addf([D.mulf([S(0), S(1)]), S(2)])
            elif op == 'lrp': v = D.addf([D.mulf([S(0), D.addf([S(1), D.neg(S(2))])]), S(2)])
            elif op in ('rcp', 'rsq', 'exp', 'log', 'frc', 'abs'):
                x = src(ss[0], 0) if op in ('rcp', 'rsq', 'exp', 'log') else S(0)
                if op == 'exp':
                    n = D.nodes[x]; v = None
                    if n[0] == 'mul':
                        lg = [t for t in n[1:] if D.nodes[t][0] == 'log2']
                        if lg:
                            rest = [t for t in n[1:] if t != lg[0]]
                            v = D.mk('pow', D.nodes[lg[0]][1], D.mulf(rest) if rest else D.leaf('lit', 1.0))
                    if v is None: v = D.mk('exp2', x)
                elif op == 'log': v = D.mk('log2', x)
                else: v = D.mk(op, x)
            elif op == 'pow': v = D.mk('pow', src(ss[0], 0), src(ss[1], 0))
            elif op in ('min', 'max'):
                x, y = S(0), S(1); v = x if x == y else D.mk(op, *sorted([x, y]))
            elif op in ('slt', 'sge', 'cmp'): v = D.mk(op, *[S(n_) for n_ in range(len(ss))])
            elif op in ('dp3', 'dp4'):
                n = 3 if op == 'dp3' else 4
                v = D.addf([D.mulf([src(ss[0], c), src(ss[1], c)]) for c in range(n)])
            elif op == 'dp2add': v = D.addf([D.mulf([src(ss[0], 0), src(ss[1], 0)]), D.mulf([src(ss[0], 1), src(ss[1], 1)]), src(ss[2], 0)])
            else: v = D.mk('op_' + op, *[src(o, c) for o in ss for c in range(4)])
            if d.mod & 1: v = D.mk('sat', v)
            if d.shift:
                s = d.shift if d.shift < 8 else d.shift - 16; v = D.mulf([v, D.leaf('lit', 2.0 ** s)])
            out[k] = v
        for k, v in out.items(): env[(d.num, k)] = v
        log.append((a + idx, i, dict(out)))
    return D, env, log

def show(D, n, depth=4, names=None):
    t = D.nodes[n]
    if t[0] == 'L':
        k = t[1]
        if k == 'mp': return '%sc%d.%s' % ((names or {}).get('mp', 'P:'), t[2], 'xyzw'[t[3]])
        if k == 'in': return 'in'
        if k == 'k': return 'k%d.%s' % (t[3], 'xyzw'[t[4]])
        if k == 'lit': return '%g' % t[2]
        return '%s%s' % (k, t[2:])
    if depth == 0: return '…'
    sub = [show(D, c, depth - 1, names) for c in t[1:]]
    if t[0] == 'neg': return '-' + sub[0]
    if t[0] == 'add': return '(' + ' + '.join(sub) + ')'
    if t[0] == 'mul': return '(' + ' * '.join(sub) + ')'
    return '%s(%s)' % (t[0], ', '.join(sub))

def roles(D, roots, depth=3):
    """per ogni foglia MP: insieme di catene ascendenti. Posizione: add/mul -> segno del termine; pow -> 'base'/'exp'; altro -> indice."""
    parents = collections.defaultdict(set)
    seen = set(); st = list(roots)
    while st:
        n = st.pop()
        if n in seen: continue
        seen.add(n)
        t = D.nodes[n]
        if t[0] == 'L': continue
        for pos, c in enumerate(t[1:]):
            if t[0] == 'pow': role = ('base', 'exp')[pos]
            elif t[0] in ('add', 'mul'): role = 'term'
            elif t[0] in ('max', 'min'): role = 'arg'
            else: role = str(pos)
            parents[c].add((n, t[0], role)); st.append(c)
    out = collections.defaultdict(set)
    def up(n, d, chain):
        ps = parents.get(n, ())
        if d == 0 or not ps: out_sink.add(chain); return
        for (p, op, role) in sorted(ps):
            # segno: il nodo e' negato dentro un add/mul?
            up(p, d - 1, chain + ((op, role),))
    for n in seen:
        t = D.nodes[n]
        if t[0] == 'L' and t[1] == 'mp':
            out_sink = set(); up(n, depth, ()); out[(t[2], t[3])] = out_sink
    return out
