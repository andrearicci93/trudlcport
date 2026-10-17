"""Prepara lo stage della baseline candidata B88_fullpass (da B87_materiali19): SOLO file cambiati, stessi percorsi relativi di mods/.
 1) lib acqua/cascata (build_unlit): 4 DRM da out_unlit/mods.
 2) fix IDR: DTP 21176 +0x180 di dlc1_uo_pillar_of_doom_a/b: 0x496 (DTP 1174, assente dal DRM, 2100 B) -> 0xe32 (DTP 3634 = Xbox 1039, presente nel DRM)."""
import sys, os, shutil, struct, hashlib, json
ROOT = '/path/to/trudlcport'
sys.path.insert(0, ROOT + '/tools')
import drm_write as DW
B87 = ROOT + '/work/baseline/B87_materiali19/mods'
ST = ROOT + '/work/ws/giro5/stage_B88b/mods'
if os.path.exists(ST): shutil.rmtree(ST)
changed = {}
U = ROOT + '/work/ws/giro5/out_unlit/mods'
for dp, _, fs in os.walk(U):
    for f in fs:
        rel = os.path.relpath(os.path.join(dp, f), U); dst = os.path.join(ST, rel); os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(os.path.join(dp, f), dst); changed[rel] = 'lib acqua/cascata (build_unlit)'
for rel in ():   # fix IDR dei pillar RITIRATO: ids(6,1039)=1174 -> il campo puo' essere un riferimento wave (tipo 6), ambiguo
    raw = open(os.path.join(B87, rel), 'rb').read(); d = DW.read(raw, 'le')
    n = 0
    for s in d.sections:
        if s.type == 7 and s.id == 21176:
            assert struct.unpack_from('<I', s.data, 0x180)[0] == 0x496, rel
            assert 3634 in {x.id for x in d.sections if x.type == 7} and 1174 not in {x.id for x in d.sections if x.type == 7}
            b = bytearray(s.data); struct.pack_into('<I', b, 0x180, 3634); s.data = bytes(b); n += 1
    assert n == 1
    out = DW.cdrm_encode(d.write('le'), 'le') if raw[:4] == b'CDRM' else d.write('le')
    # verifica: rileggendo, cambia solo quella parola
    a = {(x.type, x.id, i): x for i, x in enumerate(DW.read(raw, 'le').sections)}; bb = {(x.type, x.id, i): x for i, x in enumerate(DW.read(DW.cdrm_decode(out, 'le') if out[:4] == b'CDRM' else out, 'le').sections)} if hasattr(DW, 'cdrm_decode') else None
    dst = os.path.join(ST, rel); os.makedirs(os.path.dirname(dst), exist_ok=True); open(dst, 'wb').write(out)
    changed[rel] = 'IDR DTP 21176 +0x180: 0x496 -> 0xe32'
json.dump(changed, open(ROOT + '/work/ws/giro5/stage_B88b/changed.json', 'w'), indent=1)
for k, v in sorted(changed.items()): print(k, '|', v, hashlib.md5(open(os.path.join(ST, k), 'rb').read()).hexdigest())
