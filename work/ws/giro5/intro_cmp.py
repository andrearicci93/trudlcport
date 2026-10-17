"""Confronto Intro PC (baseline B88) vs Xbox vergine per ogni unita' DLC indicata: numero, uid (con remap +20000 dei 5 noti), nome oggetto per nome, posizioni (float s32)."""
import sys, struct, collections
sys.path.insert(0, '/path/to/trudlcport/work/ws/giro5')
from intros import *
names = sys.argv[2:]
base = sys.argv[1]
pcn = objnames(R + base + '/mods/tr8/pc-w/objectlist.txt'); xbn = objnames('/path/to/trudlcport/work/dlc1/objectlist.txt')
REMAP = {9392: 29392, 9397: 29397, 9395: 29395, 9396: 29396, 6713: 26713}
for name in names:
    P = pc_intros(base, name); X = xbox_intros(name)
    if X is None: print(name, 'Xbox non trovato'); continue
    xn = collections.Counter(xbn.get(i['obj'], '?') for i in X); pn = collections.Counter(pcn.get(i['obj'], '?') for i in P)
    xu = {REMAP.get(i['uid'], i['uid']) for i in X}; pu = {i['uid'] for i in P}
    # posizioni per uid
    xp = {REMAP.get(i['uid'], i['uid']): struct.unpack_from('>3f', i['raw'], 0x30) for i in X}; pp = {i['uid']: struct.unpack_from('<3f', i['raw'], 0x30) for i in P}
    movedpos = [u for u in xu & pu if max(abs(a - b) for a, b in zip(xp[u], pp[u])) > 1e-3]
    nmdiff = {k: (xn[k], pn.get(k, 0)) for k in set(xn) | set(pn) if xn.get(k, 0) != pn.get(k, 0)}
    print('%-34s intro Xbox %3d PC %3d | uid solo Xbox %s solo PC %s | pos diverse %d | nomi con conteggio diverso %s' % (
        name, len(X), len(P), sorted(xu - pu)[:6], sorted(pu - xu)[:6], len(movedpos), dict(list(nmdiff.items())[:6])))
