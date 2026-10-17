"""mat2 (B): material 21210 of dlc1_uo_bend_switches: Xbox section is byte-identical (data+reloc) to base Xbox material 4405 (3 more twins 12521/12522/18551
with the same shader tuple 279-282) but material_dlc copied its 10 vec4 1:1 (no param rule learnt for that tuple), while PC 4767 (PC twin of 4405) has 11 vec4 repacked.
Fix = use the PC twin section 4767 (data + reloc) for id 21210. Verified: outside the params block / count word the converted and twin sections are identical.
usage: tools/venv/bin/python -I tools/mat2_fix21210.py SRC.drm OUT.drm"""
import sys, os, pickle, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_write as DW, material_reslot as MR
src, out = sys.argv[1:3]
L = MR.libs(); XM, PM, DM = L['XM'], L['PM'], L['DM']
mx2p = pickle.load(open(os.path.join(MR.W, 'material_x2p.pkl'), 'rb'))
assert DM[21210] == XM[4405]
pd, pr = PM[mx2p[4405]]
D = DW.read(open(src, 'rb').read(), 'le'); n = 0
for s in D.sections:
    if s.type == 10 and s.id == 21210:
        assert len(s.data) == 1216 and bytes(s.data)[:0x58] == pd[:0x58]
        s.data = pd; s.reloc = pr; n += 1
assert n == 1
data = DW.cdrm_encode(D.write('le'), 'le'); open(out, 'wb').write(data)
print(out, 'replaced sections:', n, hashlib.md5(data).hexdigest())
