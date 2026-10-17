"""Override dello script del cancello (20736): prototipo, vtIndex e vtable; ricerca del prototipo con lo stesso nome
nelle classi della catena di ereditarieta' presenti nel DRM (Xbox grezzo e B83)."""
import sys, os, struct
H = os.path.dirname(os.path.abspath(__file__)); T = os.path.join(H, '..', '..', '..', 'tools'); sys.path.insert(0, T)
import drm, drm_reloc as R, script_conv as SC, dlc_generic as DG, generic_store
from wave_swap import raw_dlc
name = 'dlc1_uo_sluice_gate.drm'
ids = DG.DlcIds(generic_store.load(), None); M = ids.base[DG.SYM]
for side, raw, e in (('xb', raw_dlc(name)[0], 'be'), ('pc', open(os.path.join(T, '..', 'work', 'baseline', 'B83', 'mods', name), 'rb').read(), 'le')):
    E = '>' if e == 'be' else '<'
    secs = drm.sections_with_data(drm.cdrm_decode(raw, e), e)[1]
    for s in secs:
        if s['type'] != 8: continue
        d = s['data']; r = R.parse(s['reloc'], e)
        try: el = SC.elements(d, r, e)
        except Exception as ex: continue
        nm = struct.unpack_from(E + 'HH', d, 8); sup = struct.unpack_from(E + 'I', d, 0x18)[0]
        vts = struct.unpack_from(E + 'H', d, 0x3c)[0]
        protos = [(v, f[0]) for a, v, f in el.get('protos', [])]
        want = (12621, 4880) if side == 'xb' else (9573, 6447)
        hit = [(v, f) for v, f in protos if v in want]
        if s['id'] in (20736, 975, 3592) or hit:
            print(side, 'script', s['id'], 'nome', nm, 'super', sup, 'vtableSize', vts, 'n_proto', len(protos), 'trovati', hit)
