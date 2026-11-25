"""curve_proof.py - (20/11/2026) solo lettura. Prova sul base (work/generic/store.pkl) della regola unitcurve: ovunque in un DTP
tipo 7 Xbox c'e' un record (passo 0xb0: curva u16[64] a +0x24, marcatore beebbeeb a +0xac; passo 0xc0: curva a +0x34, marcatore
a +0xb8) con la curva monotona in BE, almeno 32 valori distinti e senza beeb (vera rampa), la curva PC del DTP accoppiato e' s16 (u16 scambiati uno a uno) o s32?"""
import sys, pickle, collections, struct
sys.path.insert(0, '/path/to/trudlcport/work/ws/lukas_check/inv'); import inv_common as C
S = pickle.load(open('/path/to/trudlcport/work/generic/store.pkl', 'rb')); im = C.idmap().get(7, {})
B = b'\xbe\xeb\xbe\xeb'; c = collections.Counter(); ex = []
for (t, xid), xs in S['xb_store'].items():
    if t != 7: continue
    p = S['pc_store'].get((7, im.get(xid, xid)))
    if not p or len(p['data']) != len(xs['data']): continue
    xd, pd = xs['data'], p['data']
    for cs, mk in ((0x24, 0xac), (0x34, 0xb8)):
        o = xd.find(B)
        while o >= 0:
            r = o - mk
            if o % 4 == 0 and r >= 0 and r + cs + 128 <= len(xd):
                u = struct.unpack_from('>64H', xd, r + cs)
                if all(a <= b for a, b in zip(u, u[1:])) and len(set(u)) >= 32 and 0xbeeb not in u:
                    xc, pc = xd[r + cs:r + cs + 128], pd[r + cs:r + cs + 128]
                    s16 = b''.join(bytes((xc[k + 1], xc[k], xc[k + 3], xc[k + 2])) for k in range(0, 128, 4))
                    s32 = b''.join(xc[k:k + 4][::-1] for k in range(0, 128, 4))
                    k = 's16' if pc == s16 else 's32' if pc == s32 else 'altro'
                    c[k, hex(mk)] += 1
                    if k != 's16' and len(ex) < 5: ex.append((xid, hex(r), k))
            o = xd.find(B, o + 1)
print(dict(c)); print(ex)
