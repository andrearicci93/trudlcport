"""Ricostruisce i DTP dei DRM cinstream DLC partendo dall'overlay (B44): liste comandi (cine_cmd, validato 106/106 sul base)
ed effetti (fx_apply, 3747 base escluso dall'addestramento: 2444 giuste / 4 tenute dall'overlay). Stessa dimensione, reloc
invariati; parole puntatore/idref tenute dall'overlay. uso: build_cine.py SRC_MODS OUT_DIR"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cinepairs, cine_cmd as CC, fxdtp as F, fx_apply as FA
sys.path.insert(0, cinepairs.T)
import drm_reloc as R, drm_write as DW
from archive import Archive
from names import crc
from convert_dlc import R as RR, PACKS

def build(name, src, dst, tab):
    a = Archive(RR + PACKS[0], 'be')
    X = {s['id']: s for s in cinepairs.secs(a.read(a.find(crc('xenon-w\\cinstream\\%s.drm' % name))[0]), 'be') if s['type'] == 7}
    D = DW.read(open(src, 'rb').read(), 'le')
    log = []
    for s in D.sections:
        if s.type != 7 or s.id not in X: continue
        x = X[s.id]; xd = x['data']
        if len(xd) != len(s.data): raise ValueError('dimensione diversa DTP %d' % s.id)
        r = R.parse(x['reloc'], 'be'); keep = {p for p, _ in r.internal} | {o for _, o in r.idref}
        if CC.fmt_of(xd):
            new, cl = CC.convert(xd, None, {p for p, _ in r.internal}); kind = 'comandi'
        elif F.is_fx(xd):
            new, st, unk = FA.conv_dtp(xd, x['reloc'], s.data, lambda v: FA.TM.get(v, v), tab); kind = 'effetti'
        else:
            continue
        new = bytearray(new)
        for o in keep: new[o:o + 4] = s.data[o:o + 4]
        nd = sum(new[k:k + 4] != s.data[k:k + 4] for k in range(0, len(new), 4))
        log.append('%s DTP %d (%s): %d parole cambiate su %d' % (name, s.id, kind, nd, len(new) // 4))
        s.data = bytes(new)
    open(dst, 'wb').write(DW.cdrm_encode(D.write('le'), 'le'))
    return log

if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
    tab = F.learn(F.samples())
    for nm in ('pdlc1_010_intro', 'pdlc1_030_finale'):
        for l in build(nm, os.path.join(src, 'cinstream', nm + '.drm'), os.path.join(out, nm + '.drm'), tab): print(l)
