"""Simboli (cdc::Symbol, pseudo-tipo 100) di uno script DLC: valore Xbox grezzo, valore nella B83, provenienza della
mappatura (esatta dalla mappa base / stimata). Uso: script_syms.py <file.drm> <id sezione script Xbox>"""
import sys, os, struct, collections
H = os.path.dirname(os.path.abspath(__file__)); T = os.path.join(H, '..', '..', '..', 'tools'); sys.path.insert(0, T)
import drm, drm_reloc as R, script_conv as SC, dlc_generic as DG, generic_store
from wave_swap import raw_dlc
name, sid = sys.argv[1], int(sys.argv[2])
xs = drm.sections_with_data(drm.cdrm_decode(raw_dlc(name)[0], 'be'), 'be')[1]
ps = drm.sections_with_data(drm.cdrm_decode(open(os.path.join(T, '..', 'work', 'baseline', 'B83', 'mods', name), 'rb').read(), 'le'), 'le')[1]
ids = DG.DlcIds(generic_store.load(), None); M = ids.base[DG.SYM]
x = [s for s in xs if s['type'] == 8 and s['id'] == sid][0]
pid = ids.base.get(8, {}).get(sid, ids.new.get(8, {}).get(sid, sid))
cand = [s for s in ps if s['type'] == 8 and s['size'] == x['size']]
p = next((s for s in cand if s['id'] == pid), cand[0] if len(cand) == 1 else None)
print('script Xbox', sid, 'len', x['size'], '-> PC id', p and p['id'])
W = SC.walk(x['data'], R.parse(x['reloc'], 'be'), 'be')
st = collections.Counter()
for o, lab in sorted(W.lab.items()):
    k = W.prior.get(lab, '')
    if not (isinstance(k, str) and k.startswith('id16') and k.endswith(':100')): continue
    xa, xb = struct.unpack_from('>HH', x['data'], o); pa, pb = struct.unpack_from('<HH', p['data'], o) if p else (None, None)
    halves = {'id16ab:100': ((xa, pa), (xb, pb)), 'id16a:100': ((xa, pa),), 'id16b:100': ((xb, pb),)}[k]
    for xv, pv in halves:
        if xv in (0, 0xffff): continue
        how = 'ESATTO' if xv in M else ('NUOVO_DLC(shift)' if xv > ids.xs_max else 'STIMATO')
        exp = ids.sym(xv)
        st[how] += 1
        print('%5x %-28s xbox %5d -> pc %5s  atteso %5d  %s%s' % (o, '/'.join(map(str, lab))[:28], xv, pv, exp, how, '' if pv == exp else '  <-- DIVERSO'))
print(dict(st))
