"""Record dei giunti (azioni nodo tipo 9 -> FUN_004d8000) e descrittori dell'azione 20 di un oggetto UberObject,
Xbox grezzo contro B83, parola per parola con interpretazione u32/f32/u16. Uso: joints.py <oggetto.drm> <id DTP>"""
import sys, os, struct
H = os.path.dirname(os.path.abspath(__file__)); T = os.path.join(H, '..', '..', '..', 'tools'); sys.path.insert(0, T)
import drm, drm_reloc as R
from wave_swap import raw_dlc
name, sid = sys.argv[1], int(sys.argv[2])
def load(side):
    raw, e = (open(os.path.join(T, '..', 'work', 'baseline', 'B83', 'mods', name), 'rb').read(), 'le') if side == 'pc' else (raw_dlc(name)[0], 'be')
    secs = drm.sections_with_data(drm.cdrm_decode(raw, e), e)[1]
    s = [x for x in secs if x['type'] == 7 and x['id'] == sid][0]
    return s['data'], dict(R.parse(s['reloc'], e).internal), ('<' if e == 'le' else '>')
X, P = load('xb'), load('pc')
def u(v, o): return struct.unpack_from(v[2] + 'I', v[0], o)[0]
recs = []
blk = X[1][0xc0]; pp = X[1][blk + 0xc]
for k in range(u(X, blk + 8)):
    a = pp + 0x54 * k; nd = X[1].get(a + 8)
    for j in range(u(X, a + 4)):
        o = nd + 0x1c * j; ap = X[1].get(o + 0x18)
        for q in range(u(X, o + 0x14)):
            t = ap + 16 * q; ty = u(X, t)
            if ty == 9: recs.append(('giunto parte%d N%d az%d' % (k, j, q), X[1][t + 4], 0x50))
            if ty == 20:
                recs.append(('az20 A parte%d N%d' % (k, j), X[1][t + 8], 0x10)); recs.append(('az20 B parte%d N%d' % (k, j), X[1][t + 12], 0x10))
                print('az20 arg1', u(X, t + 4), u(P, t + 4))
for lab, o, n in recs:
    print('==', lab, '@%d' % o)
    for w in range(o, o + n, 4):
        xb, pb = X[0][w:w + 4], P[0][w:w + 4]
        xu = struct.unpack('>I', xb)[0]; xf = struct.unpack('>f', xb)[0]; pu = struct.unpack('<I', pb)[0]; pf = struct.unpack('<f', pb)[0]
        rel = 'PTR' if w in X[1] else ''
        same = 'ok-s32' if xb[::-1] == pb else ('ok-raw' if xb == pb else ('s16' if xb[1::-1] + xb[3:1:-1] == pb else '??'))
        print('  +%02x xb %s (u %d f %.4g)  pc %s (u %d f %.4g)  %s %s' % (w - o, xb.hex(), xu, xf, pb.hex(), pu, pf, same, rel))
