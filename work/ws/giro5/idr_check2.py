import sys, io, contextlib, glob, os, struct
sys.path.insert(0, '/path/to/trudlcport/tools')
with contextlib.redirect_stdout(io.StringIO()):
    import dtpid_sweep as DS
    st, ids = DS.ctx()
import drm
print('ids(t,1039) per tipo:', {t: ids(t, 1039) for t in (2, 6, 7, 8, 11)})
print('ids(t,1174) per tipo (se 1174 fosse sorgente):', {t: ids(t, 1174) for t in (2, 6, 7, 8, 11)})
R = '/path/to/trudlcport/work/baseline/B87_materiali19/mods/'
for n in ('dlc1_uo_pillar_of_doom_a.drm', 'dlc1_uo_pillar_of_doom_b.drm'):
    sc = drm.sections_with_data(drm.cdrm_decode(open(R + n, 'rb').read(), 'le'), 'le')[1]
    print(n, 'sezioni con id 1174:', [(s['type'], s['id']) for s in sc if s['id'] == 1174], '| con id 3634:', [(s['type'], s['id']) for s in sc if s['id'] == 3634])
# altri DRM con DTP 21176 e valore a +0x180
for p in sorted(glob.glob(R + '**/*.drm', recursive=True)):
    try: sc = drm.sections_with_data(drm.cdrm_decode(open(p, 'rb').read(), 'le'), 'le')[1]
    except Exception: continue
    for s in sc:
        if s['type'] == 7 and s['id'] == 21176: print('DTP 21176 in', os.path.relpath(p, R), 'valore +0x180 =', hex(struct.unpack_from('<I', s['data'], 0x180)[0]))
