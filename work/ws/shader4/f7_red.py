"""F7 - prova "rosso": le lib PS nuove 2173/2720 di B73 (dlc_caverns_hall.drm) sostituite da un PS che scrive rosso pieno.
Domanda: il motore usa davvero una lib con id/hash nuovi? Se le superfici dei materiali 22587/22588/22589 (mesh 20804 della sala,
celle intorno a x 4000-5400, y 12900-18200) diventano rosse -> si'. Se restano come prima -> la lib viene ignorata.
Cambia SOLO i dati delle sezioni tipo 9 id 2173 e 2720 (stessi slot occupati); tutto il resto identico byte per byte (verificato).
uso: tools/venv/bin/python -I work/ws/shader4/f7_red.py  -> work/ws/shader4/B74red/dlc_caverns_hall.drm"""
import sys, os, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from f4_build import *

SRC73 = os.path.join(ROOT, 'work/baseline/B73/mods', DRM)
RED = 'ps_3_0\ndef c0, 1, 0, 0, 1\nmov oC0, c0\n'


def main():
    raw = open(SRC73, 'rb').read(); d = drm_write.read(raw, 'le')
    bc = sm3asm.encode(sm3asm.parse_text(RED))
    errs = f4_lint.lint(bc, True); assert not errs, errs
    hs_all, _ = all_hashes(); taken = set(hs_all)
    done = []
    for s in d.sections:
        if s.type == 9 and s.id in (2173, 2720):
            lib = shaderlib.parse(s.data, 'le')
            slot_bcs = [None if x == 0xffffffff else bc for x in lib['slots']]
            sec, hs = build_lib(slot_bcs, taken)
            s.data = sec; done.append((s.id, hs, lib['slots']))
    assert sorted(x[0] for x in done) == [2173, 2720], done
    out_raw = d.write('le')
    a = {(s.type, s.id): s for s in drm_write.read(raw, 'le').sections}; b = {(s.type, s.id): s for s in drm_write.read(out_raw, 'le').sections}
    assert set(a) == set(b)
    for k in a:
        if k in ((9, 2173), (9, 2720)): continue
        assert (a[k].data, a[k].reloc, a[k].flags, a[k].ver, a[k].spec, a[k].pad) == (b[k].data, b[k].reloc, b[k].flags, b[k].ver, b[k].spec, b[k].pad), k
    od = os.path.join(HERE, 'B74red'); os.makedirs(od, exist_ok=True)
    enc = drm_write.cdrm_encode(out_raw, 'le'); p = os.path.join(od, DRM); open(p, 'wb').write(enc)
    print('scritto', p, len(enc), hashlib.md5(enc).hexdigest())
    for i, hs, sl in done: print('  lib', i, 'slot', sl, 'hash', hs)


if __name__ == '__main__':
    main()
