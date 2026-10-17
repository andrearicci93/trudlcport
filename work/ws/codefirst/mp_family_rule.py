"""Task 3 - regola MaterialParams per famiglia (xs, pd): istruzioni del blocco luci che leggono c100..c115, in Xbox (xs, tradotto
senza ottimizzazione) e in PC (pd), con i valori dei materiali ponte. Uso: mp_family_rule.py XS PD  (sola lettura, nessuna scrittura in shader4)."""
import sys
S4 = '/path/to/trudlcport/work/ws/shader4'; sys.path.insert(0, S4)
from f9_transplant import *
import f9_common


def mp_instrs(prog, a, b):
    st = stypes(prog); out = []
    for k, i in enumerate(body(prog)[a:b]):
        for j, o in enumerate(i.ops):
            if not o.isdst and o.rtype == sm3asm.RT_CONST and 100 <= o.num < 116:
                out.append((a + k, i)); break
    return out


def txt(i, prog):
    return sm3asm.fmt_instr(i, prog.kind, prog.major)


def load(xs, pd):
    L = libs(); X, P = L['X'], L['P']
    xsblob = X[xs]['entries'][X[xs]['slots'][0]]['blob']; pdblob = P[pd]['entries'][P[pd]['slots'][0]]['blob']
    pprog = decode_pc(pdblob); pct = pc_ctab(pdblob); preg = {n: ri for n, rs, ri, rc in pct if rs == 3}
    K = Consts(pct)
    sprog, s0, s1, trs = translate_x(xsblob, K.fn, xsamp(xsblob, preg), xbools(xsblob))
    p0, p1 = pc_light_block(pprog)
    return sprog, s0, s1, pprog, p0, p1


def main():
    xs, pd = int(sys.argv[1]), int(sys.argv[2])
    sprog, s0, s1, pprog, p0, p1 = load(xs, pd)
    br = material_pairs(xs, pd)
    print('=== famiglia (%d,%d): %d materiali ponte; blocco Xs [%d,%d) blocco Pd [%d,%d)' % (xs, pd, len(br), s0, s1, p0, p1))
    for mx, mp, XP, PP in br[:2]:
        print(' ponte Xbox %d / PC %d' % (mx, mp))
        for i in range(max(len(XP), len(PP))):
            f = lambda r: '[' + ' '.join('%.4g' % v for v in r) + ']'
            print('   c%d  Xbox %-44s PC %s' % (100 + i, f(XP[i]) if i < len(XP) else '-', f(PP[i]) if i < len(PP) else '-'))
    print('\n--- Xs: istruzioni del blocco luci che leggono MaterialParams (indice body)')
    for k, i in mp_instrs(sprog, s0, s1): print('  %4d  %s' % (k, txt(i, sprog)))
    print('\n--- Pd: istruzioni del blocco luci che leggono MaterialParams')
    for k, i in mp_instrs(pprog, p0, p1): print('  %4d  %s' % (k, txt(i, pprog)))


if __name__ == '__main__':
    main()
