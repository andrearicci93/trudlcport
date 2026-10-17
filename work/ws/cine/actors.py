"""Attori dell'intestazione CINE (blocco 0 del .mul) vs intro dell'unita' e oggetti: replica statica di ReadyToPlay
(tru.exe FUN_00454490: per ogni attore, istanza esistente OPPURE intro nell'unita' della cine con oggetto caricato)."""
import sys, os, struct, collections
T = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'); sys.path.insert(0, T)
sys.path.insert(0, os.path.join(T, '..', 'work', 'ws', 'progress'))
import mul_convert as M, drm
import unit_ids as U
base = sys.argv[1]; cine = sys.argv[2]; units = sys.argv[3].split(',')
pd = open(os.path.join(base, 'mods', 'cinstream', cine + '.mul'), 'rb').read()
B = M.blocks(pd, '<'); c0 = [b for b in B if b[0] == 1][0][3]
W = struct.unpack_from('<%dI' % (len(c0) // 4), c0, 0)
print('scena', c0[0xc:0x4c].split(b'\0')[0], 'blocco0', len(c0), 'parole[19..24]', W[0x4c//4:0x4c//4+6])
cand = [(4 * k, W[k]) for k in range(0x4c // 4, len(W) - 1) if 4096 <= W[k] < 0x100000 and W[k + 1] == 0xffffffff]
print('id attore candidati ({..,ID,-1}):', [(hex(o), v) for o, v in cand])
names = {}
for l in open(os.path.join(base, 'mods', 'tr8', 'pc-w', 'objectlist.txt'), errors='ignore'):
    p = l.split(',', 1)
    if len(p) == 2 and p[0].strip().isdigit(): names[int(p[0])] = p[1].strip()
for u in units:
    f = os.path.join(base, 'mods', u + '.drm')
    sc = drm.sections_with_data(drm.cdrm_decode(open(f, 'rb').read(), 'le'), 'le')[1]
    L = U.level_info(sc, 'le')
    intr = {}
    for si, o in L['intros']:
        d = sc[si]['data']; intr[struct.unpack_from('<I', d, o + 0x58)[0]] = struct.unpack_from('<H', d, o + 0x50)[0]
    print('unita', u, 'intro', len(intr))
    for o, v in cand:
        if v in intr: print('   attore', v, '-> intro in', u, 'oggetto', intr[v], names.get(intr[v], '?'))
    for v in (9972,):
        print('   intro livello', v, '->', intr.get(v), names.get(intr.get(v), '?'))
