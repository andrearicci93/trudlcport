"""Intro di un'unita' (PC B83 o Xbox grezzo): oggetto, campi utili e blob dati d'istanza (Intro+0x78).
Uso: intros.py <unita'.drm> [pc|xb] [filtro_nome]"""
import sys, os, struct
H = os.path.dirname(os.path.abspath(__file__)); T = os.path.join(H, '..', '..', '..', 'tools'); sys.path.insert(0, T)
import drm, drm_reloc as R, unit_ids as U, objlists
B83 = os.path.join(T, '..', 'work', 'baseline', 'B83', 'mods')
def names(side='pc'):
    """id oggetto -> nome (objectlist.txt della B83; gli id oggetto DLC sono gli stessi su Xbox per costruzione del merge)"""
    L = open(os.path.join(B83, 'tr8', 'pc-w', 'objectlist.txt'), encoding='latin1').read().split('\n')[1:]
    return {int(a): b.strip() for a, b in (l.split(',', 1) for l in L if ',' in l)}
def load(name, side):
    if side == 'pc': return drm.sections_with_data(drm.cdrm_decode(open(os.path.join(B83, name), 'rb').read(), 'le'), 'le')[1], 'le'
    from wave_swap import raw_dlc; xr, _ = raw_dlc(name)
    return drm.sections_with_data(drm.cdrm_decode(xr, 'be'), 'be')[1], 'be'
def intros(sc, e):
    E = '>' if e == 'be' else '<'; L = U.level_info(sc, e); out = []
    for si, o in L['intros']:
        s = sc[si]; r = R.parse(s['reloc'], e); it = dict(r.internal); d = s['data']
        t = it.get(o + 0x78); blob = None; sl = set()
        if t is not None:
            tg = sorted(set(it.values()) | {len(d)}); end = min(x for x in tg if x > t)
            blob = (t, end); sl = {a: it[a] for a in it if t <= a < end}
        out.append(dict(sec=s, off=o, rec=d[o:o + 0x90], blob=blob, ptrs=sl, E=E))
    return out
if __name__ == '__main__':
    unit, side = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else 'pc'); flt = sys.argv[3] if len(sys.argv) > 3 else ''
    N = names(side); sc, e = load(unit, side)
    for k, I in enumerate(intros(sc, e)):
        E = I['E']; oid = struct.unpack_from(E + 'H', I['rec'], 0x50)[0]; nm = N.get(oid, '?')
        if flt and flt not in nm: continue
        w = struct.unpack_from(E + '36I', I['rec'])
        iid = struct.unpack_from(E + 'H', I['rec'], 0x58)[0]
        print(k, 'intro', iid, 'obj', oid, nm, 'blob', I['blob'] and (I['blob'][1] - I['blob'][0]))
        if I['blob']:
            t0, t1 = I['blob']; d = I['sec']['data']
            print('   blob', ' '.join('%08x' % x for x in struct.unpack_from(E + '%dI' % ((t1 - t0) // 4), d, t0)), 'ptr', {a - t0: b - t0 for a, b in I['ptrs'].items()})
        print('   rec', ' '.join('%x' % x for x in w))
