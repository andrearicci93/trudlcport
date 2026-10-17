"""mat2 (A): material 21164 texture-slot alignment between dlc1_uo_dragon_slider and dlc1_ei_grapple_wall.
Usage: tools/venv/bin/python -I tools/mat2_slot21164.py SRC.drm OUT.drm {rule|xbox}
  rule = slots of material_reslot.dlc_reslot (name-exact, == PC base layout 4790->5152); xbox = Xbox slots 1:1 (glitchfix2_ab_ring look).
Only the 3 slot bytes (0x4fc,0x50c,0x51c) of the type-10 section 21164 change; everything else is re-serialised unchanged (checked)."""
import sys, os, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_write as DW, material_reslot as MR
MID = 21164
def convert(raw, mode):
    D = DW.read(raw, 'le'); n = 0
    for s in D.sections:
        if s.type == 10 and s.id == MID:
            if mode == 'rule':
                b0 = bytearray(s.data)            # reslot needs Xbox slots as input: reset them first
                xd, xr = MR.libs()['DM'][MID]
                import drm_reloc as R
                xe = MR.tex_entries(xd, R.parse(xr, 'be'), '>'); pe = MR.tex_entries(bytes(b0), R.parse(s.reloc, 'le'), '<')
                for (o, t, ty, sl), (xo, xt, xty, xsl) in zip(pe, xe): b0[o + 13] = xsl
                nd, ch = MR.dlc_reslot(MID, bytes(b0), s.reloc)
                assert ch is not None
            else:
                xd, xr = MR.libs()['DM'][MID]
                import drm_reloc as R, struct
                xe = MR.tex_entries(xd, R.parse(xr, 'be'), '>')
                pe = MR.tex_entries(bytes(s.data), R.parse(s.reloc, 'le'), '<')
                b = bytearray(s.data)
                for (o, t, ty, sl), (xo, xt, xty, xsl) in zip(pe, xe): assert ty == xty; b[o + 13] = xsl
                nd = bytes(b)
            n = sum(1 for i in range(len(nd)) if nd[i] != s.data[i]); s.data = nd
    return D, n
if __name__ == '__main__':
    src, out, mode = sys.argv[1:4]
    raw = open(src, 'rb').read(); D, n = convert(raw, mode)
    data = DW.cdrm_encode(D.write('le'), 'le'); open(out, 'wb').write(data)
    print(out, 'bytes changed in 21164:', n, hashlib.md5(data).hexdigest())
