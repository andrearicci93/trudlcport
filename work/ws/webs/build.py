"""webs: web_cutout esteso ai DRM dungeon (nuovi file in work/ws/webs/out/). Idempotente: salta 6610 gia' DXT5 e materiali gia' 240-243.
usage: tools/venv/bin/python -I work/ws/webs/build.py [--mats-only|--tex-only]"""
import sys, os, struct, hashlib, json
sys.path.insert(0, 'tools')
import drm_write as DW, drm_reloc as R, tex_convert as TC, material_reslot as MR, shader_map as SM
import web_cutout as WC
OLD = {(1762, 1763, 1764, 1765)}
WEBMATS = {20676, 20673, 23173, 23329, 20876}
def patch(raw, do_tex=True, do_mat=True):
    Lb = MR.libs(); ref = Lb['PM'][WC.REF]
    D = DW.read(raw, 'le'); rep = []
    ids5 = {s.id for s in D.sections if s.type == 5}
    for s in D.sections:
        if do_mat and s.type == 10 and s.id in WEBMATS:
            tup = struct.unpack_from('<4I', s.data, 0x28)
            if tup == WC.TUPLE: rep.append(('material', s.id, 'gia 240-243, skip')); continue
            assert tup in OLD, (s.id, tup)
            nd, p, newp = WC.patch_material(s.data, s.reloc, ref)
            assert SM.vs_inputs(nd, s.reloc, '<') == SM.vs_inputs(*ref, '<')
            assert 255 in ids5, 'texture 255 assente'
            s.data = nd; rep.append(('material', s.id, 'old %s -> 240-243' % (tup,)))
        elif do_tex and s.type == 5 and s.id in WC.LUMA_TEX:
            kind = TC.pc_kind(TC.parse_pc(s.data)['fmt'])
            if kind != 'DXT1': rep.append(('texture', s.id, kind + ' skip')); continue
            s.data, n3 = WC.luma_alpha_dxt5(s.data); rep.append(('texture', s.id, 'DXT1->DXT5 (3col blocks %d)' % n3))
    return D.write('le'), rep
