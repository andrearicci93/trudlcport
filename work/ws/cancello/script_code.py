"""Parole di codice di uno script: Xbox (BE) contro B83 (LE), con etichetta del walker e reloc.
Uso: script_code.py <file.drm> <id script>"""
import sys, os, struct
H = os.path.dirname(os.path.abspath(__file__)); T = os.path.join(H, '..', '..', '..', 'tools'); sys.path.insert(0, T)
import drm, drm_reloc as R, script_conv as SC
from wave_swap import raw_dlc
name, sid = sys.argv[1], int(sys.argv[2])
xs = drm.sections_with_data(drm.cdrm_decode(raw_dlc(name)[0], 'be'), 'be')[1]
ps = drm.sections_with_data(drm.cdrm_decode(open(os.path.join(T, '..', 'work', 'baseline', 'B83', 'mods', name), 'rb').read(), 'le'), 'le')[1]
x = [s for s in xs if s['type'] == 8 and s['id'] == sid][0]; p = [s for s in ps if s['type'] == 8 and s['id'] == sid][0]
xr, pr = R.parse(x['reloc'], 'be'), R.parse(p['reloc'], 'le')
W = SC.walk(x['data'], xr, 'be'); xi, pi = dict(xr.internal), dict(pr.internal)
xid, pid = xr.id_offsets(), pr.id_offsets()
xe = {s: (si, dd) for si, s, dd in xr.external}; pe = {s: (si, dd) for si, s, dd in pr.external}
def ext(secs, e): return lambda o: e.get(o) and (secs[e[o][0]]['type'], secs[e[o][0]]['id'], e[o][1])
xx, px = ext(xs, xe), ext(ps, pe)
for o in range(0, x['size'] - 3, 4):
    lab = W.lab.get(o, ('unk',))
    if 'code' not in str(lab): continue
    a = struct.unpack_from('>I', x['data'], o)[0]; b = struct.unpack_from('<I', p['data'], o)[0]
    tag = ('ptr->%d' % xi[o]) if o in xi else ('ID%d:%d' % (xid[o], a) if o in xid else (('EXT%s' % (xx(o),)) if xx(o) else ''))
    ptag = ('ptr->%d' % pi[o]) if o in pi else ('ID%d:%d' % (pid[o], b) if o in pid else (('EXT%s' % (px(o),)) if px(o) else ''))
    print('%4x op %3d/%3d  xbox %08x  pc %08x  %-14s %-14s %s %s' % (o, a >> 24, b >> 24, a, b, tag, ptag, '/'.join(map(str, lab))[:30], '' if (a == b or tag) else '<-- diverso'))
