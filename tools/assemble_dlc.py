"""Assemble a PC DRM from an Xbox DRM (base game or DLC) using all converters.

assemble(raw_xbox, ids, store, shader_src, wave='silence', pc_copy=True, template=True)
  -> (pc_drm_bytes_cdrm, report dict)

Pipeline = dlc_generic.convert_drm with a media callback that
  * type 5  textures      -> tex_convert.convert
  * type 6  waves         -> wave_convert.silence_for_xbox_wave (wave='silence') or xbox_wave_to_pc
  * type 10 materials     -> material_dlc.material_for_writer (shader fallback + texture id remap)
  * type 12 meshes/terr.  -> mesh_convert / terrain_convert
  * type 9  shader libs   -> dropped; the PC ShaderLib sections the converted materials reference (data at 0x28..0x37)
                             are appended from shader_src(pc_shader_id) -> dict(data, reloc, ver, flags, spec)
After that the external-reloc section indices are remapped for the removed/added sections.
Hard gate: report['bad'] lists any media_passthrough / media_error route for types 5,6,10,12.
Run with: tools/venv/bin/python -I tools/assemble_dlc.py  (numpy needed for textures/meshes)
"""
import sys, os, struct, collections, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drm_reloc as R
import drm_write as DW
import dlc_generic as DG
from drm import cdrm_decode, sections_with_data

W = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'work')
SHADER = 9

def make_media(wave='silence', material='dlc'):
    def media(t, s, nid, ids):
        xd, xr = s['data'], s['reloc']
        if t == SHADER:
            return b'', b''                      # placeholder, dropped later
        if t == 10 and material == 'dlc':
            import material_dlc
            return material_dlc.material_for_writer(s['id'], xd, xr, lambda x: ids(5, x))
        return DG.default_media(t, s, nid, ids, wave=wave)
    return media

def _remap_ext(sec, newidx, removed):
    if not sec.reloc:
        return sec
    r = R.parse(sec.reloc, 'le')
    if not r.external:
        return sec
    ext = []
    for si, so, do in r.external:
        if si in removed:
            raise ValueError('external reloc targets removed shader section %d' % si)
        ext.append((newidx[si], so, do))
    r.external = ext
    sec.reloc = R.write(r, 'le')
    return sec

def assemble(raw_xbox, ids, store, shader_src, wave='silence', pc_copy=True, template=True, keep_shaders=False, material='dlc', reauthored=True):
    X = DW.read(raw_xbox, 'be')
    h, xsecs = sections_with_data(cdrm_decode(raw_xbox, 'be'), 'be')
    import contextlib, analog_idcoin      # guard: analog id-coincidence (dungeon_main DTP 23793-96 +0x10: 8 -> 213, crash 0x5c019f)
    with (analog_idcoin.guarded() if material == 'dlc' else contextlib.nullcontext()):
        secs, rep = DG.convert_drm(xsecs, ids, store, make_media(wave, material), use_pc_copy=pc_copy, use_template=template,
                                   use_pc_reauthored=reauthored, extra_fixes=(material == 'dlc'))
    routes = collections.Counter((t, route) for _, t, _, _, route in rep)
    bad = [(k, t, xid, route) for k, t, xid, nid, route in rep
           if t in (5, 6, 10, 12) and (route.startswith('media_error') or route == 'media_passthrough')]
    removed = {k for k, s in enumerate(secs) if s.type == SHADER}
    kept = [k for k in range(len(secs)) if k not in removed]
    newidx = {k: j for j, k in enumerate(kept)}
    out = [_remap_ext(secs[k], newidx, removed) for k in kept]
    need = []
    for s in out:
        if s.type == 10:
            for v in struct.unpack_from('<4I', s.data, 0x28):
                if v and v not in need:
                    need.append(v)
    missing = []
    if not keep_shaders:
        for sid in sorted(need):
            rec = shader_src(sid)
            if rec is None:
                missing.append(sid); continue
            out.append(DW.Section(SHADER, sid, rec['data'], rec['reloc'], rec['flags'], rec['ver'], rec['spec']))
    names = X.names.replace(b'xenon-w', b'pc-w')
    D = DW.Drm(out, names, X.pad, X.ver, X.u0, X.u1)
    raw = D.write('le')
    return DW.cdrm_encode(raw, 'le'), dict(routes=routes, bad=bad, need_shaders=len(need), missing_shaders=missing,
                                           removed=len(removed), nsec=len(out), names=names)

_PCSH = None
def dlc_shader_src(sid):
    global _PCSH
    if _PCSH is None:
        _PCSH = pickle.load(open(os.path.join(W, 'render', 'pc_shader_sections.pkl'), 'rb'))
    return _PCSH.get(sid)
