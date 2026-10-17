"""Parser ESATTO dell'intestazione CINE (blocco 0 del .mul) come tru.exe FUN_00456580:
@0x4c: unit, n1, n1 x {3 parole}, nAttori, per attore: id, w4, A, wC, A x {matrice 16 parole} (FUN_00453630), B, w18, B x {6 parole}, w20, w24."""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
import mul_convert as M
def parse(c0, E='<'):
    W = struct.unpack_from(E + '%dI' % (len(c0) // 4), c0, 0); k = 0x4c // 4
    unit = W[k]; n1 = W[k + 1]; recs = [W[k + 2 + 3 * i:k + 5 + 3 * i] for i in range(n1)]; k += 2 + 3 * n1
    na = W[k]; k += 1; actors = []
    for _ in range(na):
        a = dict(off=4 * k, id=W[k], w4=W[k + 1], A=W[k + 2], wC=W[k + 3]); k += 4
        assert a['A'] < 1000, a
        k += 16 * a['A']
        a['B'], a['w18'] = W[k], W[k + 1]; k += 2
        assert a['B'] < 100000, a
        a['subs'] = [W[k + 6 * j:k + 6 * j + 6] for j in range(a['B'])]; k += 6 * a['B']
        a['w20'], a['w24'] = W[k], W[k + 1]; k += 2
        actors.append(a)
    n48 = W[k]; l48 = W[k + 1:k + 1 + n48]; k += 1 + n48
    w74, n70 = W[k], W[k + 1]; k += 2
    ev = [W[k + 2 * i:k + 2 * i + 2] for i in range(n70)]; k += 2 * n70
    parse.extra = dict(n48=n48, l48=l48, w74=w74, events=ev)
    return unit, recs, actors, 4 * k
if __name__ == '__main__':
    for f, E in ((sys.argv[1], '<'),) + (((sys.argv[2], '>'),) if len(sys.argv) > 2 else ()):
        d = open(f, 'rb').read()
        c0 = [b for b in M.blocks(d, E) if b[0] == 1][0][3]
        u, recs, acts, end = parse(c0, E)
        print(f, 'unit', u, 'recs', recs, 'attori', len(acts), 'fine header @', hex(end))
        print('   extra', parse.extra)
        for a in acts:
            print('  @%x id=%d w4=%d A=%d wC=%d B=%d w18=%d w20=%d w24=%d' % (a['off'], a['id'] if a['id'] < 2**31 else a['id'] - 2**32, a['w4'], a['A'], a['wC'], a['B'], a['w18'], a['w20'], a['w24']))
