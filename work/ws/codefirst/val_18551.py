"""Task 1.4: materiale base 18551 (c106.z = 2.0) di (281,337): T costruito con donatore (164,207) valutato con TUTTI i materiali ponte della coppia (nmat illimitato), luci on/off/mix."""
import sys; sys.path.insert(0, '/path/to/trudlcport/work/ws/codefirst')
from task3_validate import *
import mp_resolve, struct_resolve
xs, pd = 164, 207
res, ties = mp_resolve.resolve(xs, pd); res, ties, _ = struct_resolve.apply(xs, pd, res, ties)
L = libs(); X, P = L['X'], L['P']
for xb, pb in ((281, 337), (164, 207), (921, 1710), (1888, 1547), (1409, 1038)):
    mt = material_pairs(xb, pb)
    xblob = X[xb]['entries'][X[xb]['slots'][0]]['blob']; xsblob = X[xs]['entries'][X[xs]['slots'][0]]['blob']
    pdblob = P[pd]['entries'][P[pd]['slots'][0]]['blob']; pbblob = P[pb]['entries'][P[pb]['slots'][0]]['blob']
    mb = material_pairs(xs, pd); pbct = pc_ctab(pbblob); xnames = {n: ri for n, rs, ri, rc in pbct if rs == 3}
    progT, info = build(xblob, pdblob, xsblob, [(m[2], m[3]) for m in mb], x_samp_names=xnames, log=[], mp_res=res)
    progP = decode_pc(pbblob)
    rows = []
    for m in mt:
        sc = {lab: compare_virt(progT, info['virt'], progP, m[2], m[3], bools=bl) for lab, bl in (('on', ALLB), ('off', {}), ('mix', {0: True, 3: True, 6: True}))}
        rows.append((m[0], m[1], PPz(m[3]) if False else m[3][6][2], sc))
    bad = [r for r in rows if min(r[3].values()) < 0.999]
    print('(%d,%d): %d materiali ponte testati, <0.999: %d; materiale 18551 %s' % (xb, pb, len(rows), len(bad), [ (r[0], r[2], r[3]) for r in rows if r[0] == 18551 or r[1] == 18551]), flush=True)
    for r in bad[:6]: print('   KO', r)
    print('   valori c106.z visti:', sorted({r[2] for r in rows}), flush=True)
