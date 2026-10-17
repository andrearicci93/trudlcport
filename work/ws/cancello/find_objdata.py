"""Cerca nei DRM la struttura letta come instance+0x50 dal codice PC (FUN_004d77a0 / FUN_004d3da0):
+8 n_link, +0xc ptr link (0x54 B), +0x10 n_liste, +0x14 ptr liste (12 B {?, n, ptr->12 B {link,tipo,valore}}),
+0x18 n_trig, +0x1c ptr trig (0x1c B), +0x30 n_spawn, +0x34 ptr. Uso: find_objdata.py <file.drm> [pc|xb]"""
import sys, os, struct
T = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'tools'); sys.path.insert(0, T)
import drm, drm_reloc as R

def load(name, side):
    if side == 'pc':
        p = os.path.join(T, '..', 'work', 'baseline', 'B83', 'mods', name)
        return drm.sections_with_data(drm.cdrm_decode(open(p, 'rb').read(), 'le'), 'le')[1], '<'
    from wave_swap import raw_dlc
    xr, _ = raw_dlc(name)
    return drm.sections_with_data(drm.cdrm_decode(xr, 'be'), 'be')[1], '>'

def scan(secs, e):
    out = []
    for s in secs:
        d = s['data']
        if len(d) < 0x38: continue
        r = R.parse(s['reloc'], 'le' if e == '<' else 'be'); it = dict(r.internal)
        nl, = struct.unpack_from(e + 'I', d, 8); nc, = struct.unpack_from(e + 'I', d, 0x10)
        if not (0 <= nl < 64 and 0 < nc < 64): continue
        if 0x14 not in it or (nl and 0xc not in it): continue
        out.append((s, it, nl, nc))
    return out

if __name__ == '__main__':
    name = sys.argv[1]; side = sys.argv[2] if len(sys.argv) > 2 else 'pc'
    secs, e = load(name, side)
    for s, it, nl, nc in scan(secs, e):
        d = s['data']
        print('sez', s['i'], 'tipo', s['type'], 'id', s['id'], 'len', len(d), 'n_link', nl, 'n_liste', nc,
              'n_trig', struct.unpack_from(e + 'I', d, 0x18)[0], 'n_spawn', struct.unpack_from(e + 'I', d, 0x30)[0])
        lp = it[0x14]
        for k in range(nc):
            a, n, _ = struct.unpack_from(e + 'III', d, lp + 12 * k)
            p = it.get(lp + 12 * k + 8)
            cmds = [struct.unpack_from(e + 'III', d, p + 12 * j) for j in range(n)] if p is not None else []
            print('  lista', k, 'campo0', a, 'n', n, 'comandi {link,tipo,valore}', cmds)
