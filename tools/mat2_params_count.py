"""mat2 (B): MaterialParams count coherence of converted DLC materials vs the D3D9 bytecode of their PC pixel-shader libs.
Calibration (base PC, 2248 materials): n_params(PC material) >= max over all PS permutations of passes 0..2 of
(highest c100..c131 register read + 1) in 2248/2248, == in 2233/2248 (see `calib`). MaterialParams = c100..c131 (InstanceParams c132, GlobalParams c140).
CLI: tools/venv/bin/python -I tools/mat2_params_count.py calib | scan OUT.tsv"""
import sys, os, struct, pickle, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import material_reslot as MR
from shaderlib import constants
from d3d9_consts import used_consts
LO, HI = 100, 132
_c = {}
def lib_need(lib, key):
    """[(declared CTAB count, used count)] per permutation of a PC PS lib."""
    if key in _c: return _c[key]
    res = []
    if lib is not None and lib['kind'] == 1:
        for s in sorted(set(lib['slots']) - {0xFFFFFFFF}):
            b = lib['entries'][s]['blob']
            v, c = constants(b, 'p')
            decl = max([rc for n, rs, ri, rc in c if n == 'MaterialParams' and rs == 2] or [0])
            u, rel = used_consts(b)
            uu = [r for r in u if LO <= r < HI]
            res.append((decl, (max(uu) - LO + 1) if uu else 0, bool(rel), frozenset(r - LO for r in uu)))
    _c[key] = res
    return res
def xbox_decl(lib, key):
    if key in _c: return _c[key]
    res = []
    if lib is not None and lib['kind'] == 1:
        for s in sorted(set(lib['slots']) - {0xFFFFFFFF}):
            v, c = constants(lib['entries'][s]['blob'], 'x')
            res.append(max([rc for n, rs, ri, rc in c if n == 'MaterialParams' and rs == 2] or [0]))
    _c[key] = res
    return res
def pc_need(pt, P):
    """per pass: (max used, min used over perms, max declared) for PS libs of the PC tuple."""
    out = []
    for s in pt[:3]:
        if not s or s not in P or P[s]['kind'] != 1: out.append(None); continue
        li = lib_need(P[s], ('p', s))
        if not li: out.append(None); continue
        out.append((max(i[1] for i in li), min(i[1] for i in li), max(i[0] for i in li)))
    return out
def calib():
    L = MR.libs(); P, PM = L['P'], L['PM']; st = collections.Counter()
    for pid, (d, r) in sorted(PM.items()):
        pt = struct.unpack_from('<4I', d, 0x28); n = struct.unpack_from('<I', d, 0x58)[0]
        pn = [x for x in pc_need(pt, P) if x]
        if not pn: st['no PS']+=1; continue
        umax = max(x[0] for x in pn); dmax = max(x[2] for x in pn)
        st['materials'] += 1; st['n >= used'] += n >= umax; st['n == used'] += n == umax; st['n == declared'] += n == dmax; st['used <= declared'] += umax <= dmax
        st['n < used (violations)'] += n < umax
    for k, v in sorted(st.items()): print('  %-28s %d' % (k, v))
if __name__ == '__main__':
    if sys.argv[1] == 'calib': calib()

def scan(outp):
    L = MR.libs(); X, D, P, XM, PM, DM = L['X'], L['D'], L['P'], L['XM'], L['PM'], L['DM']
    mats, msh, mx2p = MR.dlc_tables()
    rows = []
    for mid, m in sorted(mats.items()):
        if m['source'] != 'converted': continue
        pd = m['data']; pt = struct.unpack_from('<4I', pd, 0x28); n = struct.unpack_from('<I', pd, 0x58)[0]
        xd, xr = DM[mid]; xt = struct.unpack_from('>4I', xd, 0x28); nx = struct.unpack_from('>I', xd, 0x58)[0]
        pn = pc_need(pt, P)
        ok = [x for x in pn if x]
        umax = max([x[0] for x in ok] or [0]); umin = max([x[1] for x in ok] or [0])   # umin: the most demanding pass' least demanding permutation
        dmax = max([x[2] for x in ok] or [0])
        usedset = set()
        for sl in pt[:3]:
            if sl and sl in P and P[sl]['kind'] == 1:
                for i in lib_need(P[sl], ('p', sl)): usedset |= i[3]
        xl = [D.get(s, X.get(s)) if s else None for s in xt[:3]]
        xdm = [max(xbox_decl(l, ('x', s)) or [0]) for l, s in zip(xl, xt[:3]) if l is not None and l['kind'] == 1]
        xneed = max(xdm or [0])
        bm = msh.get(mid, {}).get('base_material'); bpn = None
        if bm in XM and mx2p.get(bm) in PM: bpn = struct.unpack_from('<I', PM[mx2p[bm]][0], 0x58)[0]
        cls = msh[mid] if mid in msh else {}
        flags = ';'.join(m['flags'])
        rows.append(dict(mid=mid, xt=xt[:3], pt=pt[:3], nx=nx, npc=n, xneed=xneed, umax=umax, umin=umin, dmax=dmax, bm=bm, bpn=bpn, usedset=sorted(usedset),
                         unver=any(f.startswith('UNVERIFIED') for f in m['flags']), flags=flags, passes=pn))
    return rows
if __name__ == '__main__' and sys.argv[1] == 'scan':
    rows = scan(sys.argv[2])
    st = collections.Counter()
    for r in rows:
        st[('unver' if r['unver'] else 'rule/exact', 'n>=umax' if r['npc'] >= r['umax'] else ('n>=umin' if r['npc'] >= r['umin'] else 'n<umin'))] += 1
    for k, v in sorted(st.items()): print(k, v)
    pickle.dump(rows, open(sys.argv[2], 'wb'))
