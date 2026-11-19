"""Genera i probe ps_3_0 per la forma 'mov rX.y, -cN.wwww' (rifiutata dal driver AMD nativo) e le sue varianti/aggiramenti."""
import struct, os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'probes')
F1, F0, FM = 0x3f800000, 0, 0xbf800000
SW = {'xyzw': 0xe4, 'wwww': 0xff, 'yyyy': 0x55, 'xxxx': 0x00, 'zzzz': 0xaa}
def dst(reg, mask, sat=False, rtype=0):
    return 0x80000000 | (mask << 16) | (0x100000 if sat else 0) | (rtype << 28 & 0x70000000) | reg
def src(kind, idx, sw='xyzw', mod=0):
    t = {'r': 0, 'c': 2}[kind]
    return 0x80000000 | (t << 28) | (mod << 24) | (SW[sw] << 16) | idx
OC0 = 0x800f0800
def ins(op, *t): return [(len(t) << 24) | op] + list(t)
def prog(body, consts=((0, (F1, F1, F1, F1)), (1, (F0, F0, F0, F0)))):
    w = [0xffff0300]
    for i, v in consts: w += [0x5000051, 0xa00f0000 | i] + list(v)
    for b in body: w += b
    w += [0xffff]
    return struct.pack('<%dI' % len(w), *w)
MOV, ADD, SUB, MUL, MAD = 1, 2, 3, 5, 4
def mov(d, s): return ins(MOV, d, s)
def finish(r): return mov(OC0, src('r', r))
P = {}
# --- forma sospetta e controlli
P['mov_y_negc_wwww_r19_c73'] = prog([mov(dst(19, 0xf), src('c', 0)), mov(dst(19, 2), src('c', 73, 'wwww', 1)), finish(19)], ((0, (F1,) * 4), (73, (F1,) * 4)))
P['mov_y_negc_wwww'] = prog([mov(dst(0, 0xf), src('c', 0)), mov(dst(0, 2), src('c', 0, 'wwww', 1)), finish(0)])
P['mov_full_negc_wwww'] = prog([mov(dst(0, 0xf), src('c', 0, 'wwww', 1)), finish(0)])
P['mov_y_negc_yyyy'] = prog([mov(dst(0, 0xf), src('c', 0)), mov(dst(0, 2), src('c', 0, 'yyyy', 1)), finish(0)])
P['mov_x_negc_wwww'] = prog([mov(dst(0, 0xf), src('c', 0)), mov(dst(0, 1), src('c', 0, 'wwww', 1)), finish(0)])
P['mov_xyz_negc_xyzw'] = prog([mov(dst(0, 0xf), src('c', 0)), mov(dst(0, 7), src('c', 0, 'xyzw', 1)), finish(0)])
P['mov_y_posc_wwww'] = prog([mov(dst(0, 0xf), src('c', 0)), mov(dst(0, 2), src('c', 0, 'wwww')), finish(0)])
P['mov_y_negr_wwww'] = prog([mov(dst(0, 0xf), src('c', 0)), mov(dst(1, 0xf), src('c', 0)), mov(dst(0, 2), src('r', 1, 'wwww', 1)), finish(0)])
# --- 2 costanti DIVERSE nella stessa istruzione (vera causa del rifiuto AMD: 3 'cmp' per shader del port)
CMP = 0x58
P['two_const_cmp'] = prog([mov(dst(0, 0xf), src('c', 0)), ins(CMP, dst(0, 0xf), src('c', 0), src('r', 0), src('c', 1, 'yyyy')), finish(0)])
P['two_const_add'] = prog([mov(dst(0, 0xf), src('c', 0)), ins(ADD, dst(0, 0xf), src('c', 0), src('c', 1)), finish(0)])
P['one_const_cmp'] = prog([mov(dst(0, 0xf), src('c', 0)), ins(CMP, dst(0, 0xf), src('c', 0), src('r', 0), src('c', 0, 'yyyy')), finish(0)])
P['two_const_cmp_FIXED'] = prog([mov(dst(0, 0xf), src('c', 0)), mov(dst(1, 0xf), src('c', 1)), ins(CMP, dst(0, 0xf), src('c', 0), src('r', 0), src('r', 1, 'yyyy')), finish(0)])
P['two_const_add_FIXED'] = prog([mov(dst(0, 0xf), src('c', 0)), mov(dst(1, 0xf), src('c', 1)), ins(ADD, dst(0, 0xf), src('c', 0), src('r', 1)), finish(0)])
for n, b in P.items():
    open(os.path.join(OUT, 'probe_ps_%s.bin' % n), 'wb').write(b)
print(len(P), 'probe scritti in', OUT)
