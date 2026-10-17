"""Toglie CINE_SKIP da dlc_level1_start.drm: riporta il reloc esterno di 20068 @0x6c4 da (23175, proto 1528 'warp')
a (941/PC 3523, proto 9232 vtIndex 57 = PlayCinematic). cine_nowait (non aspettare il loading screen) resta.
uso: unskip.py IN.drm OUT.drm"""
import sys, os, struct
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'))
import drm, drm_reloc as R, drm_write as DW
src, dst = sys.argv[1:3]
D = DW.read(open(src, 'rb').read(), 'le')
S = D.sections
k = next(i for i, s in enumerate(S) if (s.type, s.id) == (8, 20068))
j = next(i for i, s in enumerate(S) if (s.type, s.id) == (8, 3523))
assert struct.unpack_from('<H', S[j].data, 9232 + 6)[0] == 57, 'proto 9232 non e PlayCinematic'
assert S[k].data[0x6c0:0x6c4] == bytes.fromhex('0000006a')
r = R.parse(S[k].reloc, 'le')
e = [x for x in r.external if x[1] == 0x6c4]
assert len(e) == 1 and (S[e[0][0]].type, S[e[0][0]].id, e[0][2]) == (8, 23175, 1528), e
r.external = [(j, so, 9232) if so == 0x6c4 else (si, so, do) for si, so, do in r.external]
nr = R.write(r, 'le'); assert len(nr) == len(S[k].reloc)
S[k].reloc = nr
open(dst, 'wb').write(DW.cdrm_encode(D.write('le'), 'le'))
print('ok', dst)
